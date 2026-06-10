<template>
  <div class="content" style="padding:0;max-width:100%;flex-direction:row;gap:0">
    <div style="width:200px;min-width:200px;display:flex;flex-direction:column;border-right:1px solid var(--border);padding:12px 8px;gap:2px">
      <button @click="switchChat(chatState.newSession().id)" class="sidebar-btn" style="font-size:12px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;padding:6px 10px">＋ 新对话</button>
      <div style="flex:1;min-height:0;overflow-y:auto;display:flex;flex-direction:column;gap:2px">
        <div v-if="!chatState.sessions.length" class="empty-panel" style="padding:16px 0">暂无对话</div>
        <div v-for="s in chatState.sessions" :key="s.id" style="display:flex;align-items:center" @mouseenter="$event.currentTarget.querySelector('.del-btn').style.display='block'" @mouseleave="$event.currentTarget.querySelector('.del-btn').style.display='none'">
          <button @click="switchChat(s.id)" class="sidebar-btn" :class="{active:s.id===chatState.curId}" style="font-size:12px;text-align:left;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding:6px 10px;flex:1;min-width:0" :title="s.title">{{s.title}}</button>
          <button @click="delSession(s.id)" class="del-btn" style="display:none;padding:2px 6px;color:var(--text-3);font-size:10px;font-family:var(--mono);transition:color.12s" @mouseenter="$event.target.style.color='var(--red)'" @mouseleave="$event.target.style.color='var(--text-3)'">✕</button>
        </div>
      </div>
    </div>
    <div style="flex:1;display:flex;flex-direction:column;min-width:0;padding:0 16px">
    <div ref="scroller" class="chat-scroll">
      <div v-if="!messages.length && !ans" class="empty-state">
        <div class="empty-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
        </div>
        <p style="font-size:18px;font-weight:600">AgenticRAG</p>
        <p style="font-size:13px;max-width:400px;text-align:center;line-height:1.6;color:var(--text-3)">向量检索 + 知识图谱 + LLM 综合生成<br/>为每段回答提供可溯源证据</p>
      </div>
      <div class="chat-inner">
        <div v-for="(m, i) in messages" :key="i" class="msg" :class="{ 'msg-group': i > 0 && messages[i-1].role === m.role }">
          <div class="msg-avatar" :class="m.role">
            <svg v-if="m.role==='assistant'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          </div>
          <div class="msg-body">
            <div class="msg-text"><MarkdownViewer :content="m.content"  /><span v-if="m.time" class="msg-time">{{new Date(m.time).toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'})}}</span></div>
            <div v-if="m.evidence?.length" class="evidence-panel">
              <div class="evidence-header" @click="m._evShow = !m._evShow">
                <svg :style="{ transform: m._evShow ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform .2s cubic-bezier(.25,.46,.45,.94)' }" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 18l6-6-6-6"/></svg>
                <span>{{ m.evidence.length }} 条检索证据</span>
              </div>
              <transition name="ev-slide">
                <div v-if="m._evShow" class="evidence-list">
                  <div v-for="e in m.evidence" :key="e.id" class="evidence-item">
                  <div class="evidence-source">{{ e.source }} <span class="evidence-score">{{ (e.score*100).toFixed(0) }}% 匹配</span></div>
                  <div class="evidence-text">{{ e.text }}</div>
                </div>
              </div>
              </transition>
            </div>
          </div>
        </div>
        <div v-if="streaming" class="msg">
          <div class="msg-avatar assistant">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          </div>
          <div class="msg-body">
            <div class="msg-text">{{ ans }}<span class="cursor-blink">▍</span></div>
          </div>
        </div>
      </div>
    </div>
    <div class="chat-input-bar">
      <div class="chat-input-inner">
        <textarea v-model="input" class="query-input" placeholder="输入研究问题…" rows="1" :disabled="streaming" @keydown.enter.prevent="submit" />
        <button @click="deepMode=!deepMode" :title="deepMode?'深度模式':'快速模式'" style="padding:2px 8px;border-radius:2px;font-size:10px;font-weight:600;font-family:var(--mono);flex-shrink:0;transition:all .12s;text-transform:uppercase;letter-spacing:.5px" :style="deepMode?{background:'rgba(0,188,212,.1)',color:'#00bcd4',border:'1px solid rgba(0,188,212,.2)'}:{background:'rgba(255,255,255,.03)',color:'var(--text-3)',border:'1px solid var(--border)'}">{{deepMode?'🧠 深度':'⚡ 快速'}}</button>
        <button @click="useWeb=!useWeb" :title="useWeb?'联网已开':'联网已关'" style="padding:2px 8px;border-radius:2px;font-size:10px;font-weight:600;font-family:var(--mono);flex-shrink:0;transition:all .12s;text-transform:uppercase;letter-spacing:.5px" :style="useWeb?{background:'rgba(0,188,212,.1)',color:'#00bcd4',border:'1px solid rgba(0,188,212,.2)'}:{background:'rgba(255,255,255,.03)',color:'var(--text-3)',border:'1px solid var(--border)'}">{{useWeb?'🌐 联网':'🌐 断网'}}</button>
        <button class="query-submit" :disabled="!input.trim()||streaming" @click="submit">
          <svg v-if="!streaming" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          <span>发送</span>
        </button>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import MarkdownViewer from '../components/MarkdownViewer.vue'
import { useSSE } from '../utils/sse'
import { chatState } from '../stores/chat'

const messages = ref(chatState.messages)
watch(() => chatState.curId, () => { messages.value = chatState.messages })
const streaming = ref(false)
const ans = ref('')
const ev = ref<any[]>([])
const input = ref('')
const scroller = ref<HTMLDivElement>()
function submit() {
  const q = input.value.trim()
  if (q && !streaming.value) { send(q, useWeb.value, deepMode.value); input.value = '' }
}

function switchChat(id: string) { chatState.setCurId(id) }
function delSession(id: string) { chatState.delSession(id) }

const send = useSSE('/api/query/stream', messages, streaming, ans, ev, q => {
  const s = chatState.sessions.find(s => s.id === chatState.curId)
  if (s) { s.title = q.slice(0, 30); chatState.save() }
})
const useWeb = ref(false), deepMode = ref(false)

watch(messages, () => {
  chatState.save()
}, { deep: true })
watch(ans, () => {
  nextTick(() => scroller.value?.scrollTo({ top: scroller.value.scrollHeight, behavior: 'smooth' }))
})
</script>
