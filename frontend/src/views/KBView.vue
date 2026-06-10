<template>
  <div class="content" style="padding:0;max-width:100%">
    <div style="display:flex;flex:1;gap:16px;padding:24px;height:100%">
      <div style="width:260px;min-width:260px;padding:16px;background:rgba(15,23,42,.5);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,.04);border-radius:20px;height:fit-content">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
          <span style="font-weight:600;font-size:14px">知识库</span>
          <button @click="sf=true" class="sidebar-btn" style="width:28px;height:28px;padding:0;justify-content:center;flex-shrink:0">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          </button>
        </div>
        <div :class="'sidebar-btn'+(s?.id===kb.id?' active':'')" @click="s=kb;ld()" v-for="kb in kbs" :key="kb.id" style="padding:10px 12px">
          <div style="flex:1;min-width:0">
            <div style="font-size:13px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{kb.name}}</div>
            <div style="font-size:11px;color:var(--text-3)">{{kb.description||'无描述'}}</div>
          </div>
          <button @click.stop="dk(kb.id)" style="color:var(--text-3);flex-shrink:0;padding:2px;opacity:0;transition:opacity .15s" :style="{opacity:s?.id===kb.id?1:0}">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>
          </button>
        </div>
        <div v-if="!kbs.length" class="empty-panel">暂无知识库，点击上方 ＋ 创建</div>
      </div>

      <div v-if="!s" style="flex:1;display:flex;align-items:center;justify-content:center;color:var(--text-3);font-size:14px;gap:12px;flex-direction:column">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--text-3)" stroke-width="1" opacity=".3"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        <span>从左侧选择知识库</span>
      </div>

      <div v-else style="flex:1;display:flex;flex-direction:column;gap:16px;min-width:0">
        <div style="padding:40px 24px;border:2px dashed rgba(255,255,255,.06);border-radius:20px;text-align:center;cursor:pointer;transition:all .3s;background:rgba(15,23,42,.3);backdrop-filter:blur(8px)" @click="fi?.click()" @drop.prevent="onDrop" @dragover.prevent @mouseenter="$event.currentTarget.style.borderColor='rgba(0,188,212,.3)'" @mouseleave="$event.currentTarget.style.borderColor='rgba(255,255,255,.06)'">
          <input ref="fi" type="file" multiple accept=".pdf,.docx,.doc,.pptx,.txt,.md,.csv,.xlsx,.xls,.html,.htm,.xml,.json,.rtf,.eml,.msg,.epub,.png,.jpg,.jpeg,.tiff,.bmp,.odt,.odp,.ods" style="display:none" @change="onInput" />
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--text-3)" stroke-width="1.5" style="margin-bottom:8px"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          <p style="font-size:14px;font-weight:500;color:var(--text-2)">拖拽文件到此处或点击上传</p>
          <p style="font-size:11px;color:var(--text-3);margin-top:4px">支持 PDF / DOCX / PPTX / XLSX / TXT / MD / HTML / 图片 / 邮件 等 20+ 格式</p>
        </div>

        <div style="display:flex;gap:8px;align-items:center">
          <span style="font-weight:600;font-size:14px">{{s.name}}</span>
          <span style="font-size:12px;color:var(--text-3);font-family:var(--mono)">{{fs.length}} 文档</span>
          <button v-if="fs.length" @click="idx" class="btn-primary" style="margin-left:auto">索引</button>
        </div>

        <div v-if="msg" style="padding:8px 14px;border-radius:8px;font-size:12px;background:rgba(16,185,129,.1);color:var(--emerald);border:1px solid rgba(16,185,129,.15)">{{msg}}</div>

        <div v-if="fs.length" style="display:flex;flex-direction:column;gap:4px">
          <div v-for="f in fs" :key="f.filename" style="display:flex;align-items:center;gap:10px;padding:10px 14px;background:rgba(15,23,42,.4);border:1px solid rgba(255,255,255,.04);border-radius:12px;font-size:13px;transition:border-color .2s" @mouseenter="$event.currentTarget.style.borderColor='rgba(255,255,255,.08)'" @mouseleave="$event.currentTarget.style.borderColor='rgba(255,255,255,.04)'">
            <span style="font-size:18px">{{({'pdf':'📄','docx':'📝','pptx':'📑','txt':'📃','md':'📃','csv':'📊'} as Record<string,string>)[f.suffix.slice(1)]||'📄'}}</span>
            <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{f.filename}}</span>
            <span v-if="f.indexed" class="label-tag" style="background:rgba(0,200,83,.1);color:#00c853;border:1px solid rgba(0,200,83,.2)">已索引</span>
            <span v-else class="label-tag" style="background:rgba(255,143,0,.1);color:#ff8f00;border:1px solid rgba(255,143,0,.2)">未索引</span>
            <span style="font-size:11px;color:var(--text-3);font-family:var(--mono)">{{(f.size/1024).toFixed(1)}} KB</span>
            <button @click="dd(f.filename)" style="color:var(--text-3);padding:2px;transition:color .2s" @mouseenter="$event.target.style.color='var(--red)'" @mouseleave="$event.target.style.color='var(--text-3)'">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>
        <div v-else class="empty-panel" style="padding:40px 0">暂无文档，拖拽或点击上方区域上传</div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="sf" style="position:fixed;inset:0;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;z-index:100" @click.self="sf=false">
        <div style="background:rgba(15,23,42,.8);backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,.06);border-radius:20px;width:380px;padding:24px;animation:slideUp .3s cubic-bezier(.16,1,.3,1)">
          <p style="font-weight:600;font-size:15px;margin-bottom:16px">创建知识库</p>
          <input v-model="nn" placeholder="名称" style="width:100%;padding:10px 12px;background:rgba(30,41,59,.4);border:1px solid rgba(255,255,255,.06);border-radius:8px;color:var(--text);font-size:13px;margin-bottom:8px" />
          <input v-model="nd" placeholder="描述" style="width:100%;padding:10px 12px;background:rgba(30,41,59,.4);border:1px solid rgba(255,255,255,.06);border-radius:8px;color:var(--text);font-size:13px;margin-bottom:16px" />
          <div style="display:flex;gap:8px">
            <button @click="sf=false" class="btn-ghost" style="flex:1;padding:10px">取消</button>
            <button @click="ck" class="btn-primary" style="flex:1;padding:10px" :disabled="!nn.trim()">创建</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getKBList, clearKBCache } from '../utils/kb'
const kbs = ref<any[]>([]), s = ref<any>(null), fs = ref<any[]>([]), fi = ref<HTMLInputElement>(), msg = ref(''), sf = ref(false), nn = ref(''), nd = ref('')
const fk = async () => { kbs.value = await getKBList() }
const ld = async () => { if (!s.value) return; const r = await (await fetch(`/api/knowledge-bases/${s.value.id}/documents`)).json(); fs.value = r.documents || [] }
const ck = async () => { if (!nn.value.trim()) return; await fetch('/api/knowledge-bases', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: nn.value.trim(), description: nd.value.trim() }) }); sf.value = false; nn.value = ''; nd.value = ''; clearKBCache(); await fk() }
const dk = async (id: string) => { await fetch(`/api/knowledge-bases/${id}`, { method: 'DELETE' }); s.value = null; clearKBCache(); await fk() }
const up = async (f: FileList) => { if (!s.value) return; const fm = new FormData(); Array.from(f).forEach(x => fm.append('files', x)); await fetch(`/api/knowledge-bases/${s.value.id}/upload`, { method: 'POST', body: fm }); await ld() }
const onDrop = (e: DragEvent) => { if (e.dataTransfer?.files) up(e.dataTransfer.files) }
const onInput = (e: Event) => { const t = e.target as HTMLInputElement; if (t.files) up(t.files) }
const dd = async (fn: string) => { if (!s.value) return; await fetch(`/api/knowledge-bases/${s.value.id}/documents/${encodeURIComponent(fn)}`, { method: 'DELETE' }); await ld() }
const idx = async () => { if (!s.value) return; msg.value = '索引中...'; try { const r = await fetch(`/api/knowledge-bases/${s.value.id}/index`, { method: 'POST' }); if (!r.ok) { const e = await r.json(); msg.value = e.detail || '索引失败' } else { const d = await r.json(); let t = `完成: ${d.indexed} 分块`; if (d.failed?.length) t += `，失败: ${d.failed.join(', ')}`; if (d.skipped?.length) t += `，跳过: ${d.skipped.join(', ')}`; msg.value = t; await ld() } } catch { msg.value = '网络错误' }; setTimeout(() => msg.value = '', 5000) }
onMounted(fk)
</script>