<template>
  <div class="content" style="padding:0;max-width:100%;flex:1;display:flex;flex-direction:column;min-height:0">
    <div style="display:flex;flex-direction:column;flex:1;min-height:0">
      <div style="display:flex;align-items:center;gap:12px;padding:10px 20px;flex-shrink:0;background:var(--bg-surface);border-bottom:1px solid var(--border)">
        <span style="font-weight:700;font-size:13px;text-transform:uppercase;letter-spacing:.5px">知识图谱</span>
        <div data-graph-kb style="position:relative">
          <button @click="sd=!sd" class="sidebar-btn" style="font-size:12px;text-transform:uppercase;letter-spacing:.5px;padding:4px 10px;min-width:100px;display:flex;align-items:center;gap:6px"><span style="flex:1;text-align:left;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{kbs.find(k=>k.id===sel)?.name||'选择知识库'}}</span><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg></button>
          <div v-if="sd" style="position:absolute;top:100%;left:0;right:0;z-index:20;margin-top:2px;background:var(--bg-surface);border:1px solid var(--border);border-radius:var(--radius);padding:4px">
            <div v-for="kb in kbs" :key="kb.id" @click="sd=false;sel=kb.id;load()" class="sidebar-btn" style="font-size:12px;padding:6px 10px" :style="sel===kb.id?'background:rgba(0,188,212,.06);color:var(--cyan);border-color:rgba(0,188,212,.15)':''">{{kb.name}}</div>
          </div>
        </div>
        <button @click="build" :disabled="!sel||building" style="padding:4px 12px;border-radius:var(--radius);background:var(--cyan);color:#000;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;transition:all .2s cubic-bezier(.25,.46,.45,.94);border:1px solid transparent" @mouseenter="$event.target.style.filter='brightness(1.15)'" @mouseleave="$event.target.style.filter=''">
          <svg v-if="building" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation:spin 1s linear infinite"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"/></svg>
          <span>{{building?'构建中...':'构建图谱'}}</span>
        </button>
        <button v-if="nodes.length" @click="del" style="padding:4px 12px;border-radius:var(--radius);border:1px solid var(--border);color:var(--text-3);font-size:12px;text-transform:uppercase;letter-spacing:.5px;transition:all .2s cubic-bezier(.25,.46,.45,.94)" @mouseenter="$event.target.style.borderColor='var(--border-light)';$event.target.style.color='var(--text)'" @mouseleave="$event.target.style.borderColor='var(--border)';$event.target.style.color='var(--text-3)'">删除图谱</button>
        <button v-if="nodes.length" @click="resetZoom" style="padding:4px 12px;border-radius:var(--radius);border:1px solid var(--border);color:var(--text-3);font-size:12px;text-transform:uppercase;letter-spacing:.5px;transition:all .2s cubic-bezier(.25,.46,.45,.94)" @mouseenter="$event.target.style.borderColor='var(--border-light)';$event.target.style.color='var(--text)'" @mouseleave="$event.target.style.borderColor='var(--border)';$event.target.style.color='var(--text-3)'">重置视角</button>
        <span v-if="msg" style="font-size:12px;color:var(--amber);padding:2px 8px;background:rgba(255,143,0,.1);border-radius:2px;border:1px solid rgba(255,143,0,.2);font-family:var(--mono)">{{msg}}</span>
        <span v-if="nodes.length" style="margin-left:auto;font-size:11px;color:var(--text-3);font-family:var(--mono)">{{nodes.length}} 节点 · {{edges.length}} 关系</span>
      </div>
      <div ref="c" style="flex:1;min-height:0;cursor:grab;user-select:none;touch-action:none"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { getKBList } from '../utils/kb'
const c = ref<HTMLDivElement>(), sel = ref(''), kbs = ref<any[]>([]), nodes = ref<any[]>([]), edges = ref<any[]>([]), building = ref(false), msg = ref(''), sd = ref(false)
let _ca: HTMLCanvasElement | null = null, _draw: (() => void) | null = null, _tr: any = null
function resetZoom() { if (_ca && _draw) { _tr.x = 0; _tr.y = 0; _tr.k = 1; _draw() } }

onMounted(async () => { kbs.value = await getKBList(); document.addEventListener('click', (e:any) => { if (!e.target.closest?.('[data-graph-kb]')) sd.value = false }) })

async function load() {
  if (!sel.value) return; nodes.value = []; edges.value = []
  const r = await (await fetch(`/api/knowledge-bases/${sel.value}/graph`)).json()
  nodes.value = r.nodes || []; edges.value = r.edges || []; await nextTick(); render()
}
async function build() {
  if (!sel.value||building.value) return; building.value = true; msg.value = ''
  try { const r = await (await fetch(`/api/knowledge-bases/${sel.value}/graph/build`,{method:'POST'})).json(); msg.value = r.entities?`完成: ${r.entities} 实体, ${r.relations} 关系`:'失败'; await load() }
  catch { msg.value = '构建失败' }; building.value = false; setTimeout(() => msg.value = '', 5000)
}
async function del() {
  if (!sel.value) return; await fetch(`/api/knowledge-bases/${sel.value}/graph`,{method:'DELETE'}); nodes.value=[]; edges.value=[]; render()
}
function render() {
  const el = c.value; if (!el) return; el.innerHTML = ''
  if (!nodes.value.length) { el.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-3)">暂无图谱数据</div>'; return }
  import('d3').then(d3 => {
    const w = el.clientWidth, h = el.clientHeight, dpr = devicePixelRatio || 1
    const ca = document.createElement('canvas')
    ca.width = w * dpr; ca.height = h * dpr; ca.style.cssText = `width:${w}px;height:${h}px;display:block;touch-action:none`
    const cx = ca.getContext('2d')!; cx.scale(dpr, dpr); el.appendChild(ca); _ca = ca
    let tr = {x:0,y:0,k:1}, drg: any = null; _tr = tr

    const deg: Record<string, number> = {}; edges.value.forEach((e: any) => { deg[e.source] = (deg[e.source]||0)+1; deg[e.target] = (deg[e.target]||0)+1 })
    const md = Math.max(...Object.values(deg), 1), cl: Record<number,string> = {1:'#8B5CF6',2:'#06B6D4',3:'#10B981',4:'#F59E0B',5:'#EF4444',6:'#EC4899',7:'#14B8A6',8:'#F97316'}
    const sim = d3.forceSimulation(nodes.value).force('link', d3.forceLink(edges.value).id((d: any)=>d.id).distance(100)).force('charge', d3.forceManyBody().strength(-50)).force('center', d3.forceCenter(w/2, h/2)).force('collide', d3.forceCollide().radius((d:any)=>10+((deg[d.id]||0)/md)*12))
    const fs = 11, lh = 16

    function draw() {
      cx.clearRect(0, 0, w, h)
      cx.save(); cx.translate(tr.x, tr.y); cx.scale(tr.k, tr.k)
      // edges（去自环+平行线弯曲）
      const emap = new Map<string, {sx:number,sy:number,tx:number,ty:number}[]>()
      for (const e of edges.value) {
        const s=e.source,t=e.target; if(s.x==null||t.x==null||s.id===t.id) continue
        const k = s.id<t.id ? `${s.id}|${t.id}` : `${t.id}|${s.id}`
        if (!emap.has(k)) emap.set(k, [])
        emap.get(k)!.push({sx:s.x,sy:s.y,tx:t.x,ty:t.y})
      }
      cx.strokeStyle = 'rgba(255,255,255,.22)'; cx.lineWidth = 1.2; cx.beginPath()
      for (const ers of emap.values()) {
        if (ers.length===1) { const e=ers[0]; cx.moveTo(e.sx,e.sy); cx.lineTo(e.tx,e.ty) }
        else for (let i=0;i<ers.length;i++) {
          const e=ers[i], mx=(e.sx+e.tx)/2, my=(e.sy+e.ty)/2, dx=e.ty-e.sy, dy=e.sx-e.tx, len=Math.sqrt(dx*dx+dy*dy)||1, off=12+24*i
          cx.moveTo(e.sx,e.sy); cx.quadraticCurveTo(mx+dx/len*off, my+dy/len*off, e.tx,e.ty)
        }
      }
      cx.stroke()
      // edge labels (limit to ~30)
      cx.fillStyle = 'rgba(255,255,255,.2)'; cx.font = '9px sans-serif'; cx.textAlign = 'center'; cx.textBaseline = 'middle'
      let lc = 0
      for (const e of edges.value) {
        if (!e.label || lc++ > 30) break
        const s=e.source,t=e.target; if(s.x==null||t.x==null) continue
        cx.fillText(e.label, (s.x+t.x)/2, (s.y+t.y)/2)
      }
      // nodes
      const taken: {l:number,r:number,t:number,b:number}[] = []
      for (const n of nodes.value) {
        const r = 5 + ((deg[n.id]||0)/md)*12
        cx.beginPath(); cx.arc(n.x, n.y, r, 0, Math.PI*2)
        cx.fillStyle = cl[n.group]||'#64748B'; cx.fill()
        cx.strokeStyle = '#070B14'; cx.lineWidth = 2; cx.stroke()
        // label with collision avoidance
        const lbl = n.label||n.id, fsz = fs+((deg[n.id]||0)/md)*4
        cx.font = `${fsz}px sans-serif`; cx.textAlign = 'left'; cx.textBaseline = 'middle'
        const tw = cx.measureText(lbl).width, lx = n.x+r+8, ly = n.y, hw = tw/2, hh = fsz/2+2
        const ov = taken.some(t => lx+hw > t.l && lx-hw < t.r && ly+hh > t.t && ly-hh < t.b)
        if (!ov) { taken.push({l:lx-hw, r:lx+hw, t:ly-hh, b:ly+hh}); cx.fillStyle = '#E2E8F0'; cx.fillText(lbl, lx, ly) }
      }
      cx.restore()
    }

    function hitTest(mx: number, my: number) {
      const tx = (mx - tr.x) / tr.k, ty = (my - tr.y) / tr.k
      for (const n of nodes.value) { const r = 5 + ((deg[n.id]||0)/md)*12; if ((tx-n.x)**2 + (ty-n.y)**2 <= r*r) return n }
      return null
    }
    let isPan = false, isDrg = false, sx = 0, sy = 0, st = tr
    ca.addEventListener('pointerdown', e => {
      e.preventDefault()
      const n = hitTest(e.offsetX, e.offsetY)
      if (n) { isDrg = true; drg = n; sim.alphaTarget(.008).restart(); n.fx = n.x; n.fy = n.y }
      else { isPan = true; sx = e.clientX; sy = e.clientY; st = tr }
      ca.setPointerCapture(e.pointerId)
    })
    ca.addEventListener('pointermove', e => {
      if (isDrg && drg) { drg.fx = (e.offsetX - tr.x) / tr.k; drg.fy = (e.offsetY - tr.y) / tr.k; drg.x = drg.fx; drg.y = drg.fy; draw() }
      else if (isPan) { const dx = e.clientX - sx, dy = e.clientY - sy; tr = _tr = {x: st.x + dx, y: st.y + dy, k: st.k}; draw() }
    })
    function resetPtr(e: any) {
      if (isDrg && drg) { drg.fx = null; drg.fy = null; sim.alphaTarget(0); drg = null }
      isPan = false; isDrg = false; try { ca.releasePointerCapture(e.pointerId) } catch {}
    }
    ca.addEventListener('pointerup', resetPtr)
    ca.addEventListener('pointercancel', resetPtr)
    ca.addEventListener('pointerleave', resetPtr)
    ca.addEventListener('wheel', e => {
      e.preventDefault()
      const nk = Math.max(.3, Math.min(4, tr.k * Math.exp(-e.deltaY * .001)))
      const p = [e.offsetX, e.offsetY]
      tr = _tr = {x: p[0] - (p[0] - tr.x) * nk / tr.k, y: p[1] - (p[1] - tr.y) * nk / tr.k, k: nk}
      draw()
    }, { passive: false })

    _draw = draw
    sim.on('tick', draw)
  })
}
</script>