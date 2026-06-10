import type { Ref } from 'vue'
import type { Evidence, Message } from '../types/research'

export function useSSE(url: string, messages: Ref<Message[]>, streaming: Ref<boolean>, ans: Ref<string>, ev: Ref<Evidence[]>, onFirstMsg?: (q: string) => void) {
  let sid = '', first = true, streamingStarted = false
  let _buf = '', _timer: any = null

  function _flush() {
    if (_timer) { cancelAnimationFrame(_timer); _timer = null }
    if (_buf) { ans.value += _buf; _buf = '' }
  }

  function _push(t: string) {
    _buf += t
    if (!_timer) { _timer = requestAnimationFrame(_flush) }
  }

  return async function send(q: string, useWeb = true, deepMode = false) {
    streamingStarted = false
    _buf = ''
    if (_timer) { cancelAnimationFrame(_timer); _timer = null }
    messages.value.push({ role: 'user', content: q, time: Date.now() })
    if (first && onFirstMsg) { onFirstMsg(q); first = false }
    ans.value = ''
    ev.value = []
    streaming.value = true
    try {
      const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, conversation_id: sid, use_web: useWeb, deep_mode: deepMode }),
      })
      if (!r.ok || !r.body) return
      const reader = r.body.getReader()
      const dec = new TextDecoder()
      let buf = '', event = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += dec.decode(value, { stream: true })
        for (const line of buf.split('\n')) {
          const t = line.trim()
          if (!t) continue
          if (t.startsWith('event:')) { event = t.slice(6).trim(); continue }
          if (t.startsWith('data:')) {
            try {
              const d = JSON.parse(t.slice(5).trim())
              if (event === 'start') sid = d.conversation_id
              else if (event === 'status') { if (!streamingStarted) ans.value = d.status }
              else if (event === 'token') {
                if (!streamingStarted) { streamingStarted = true; ans.value = '' }
                _push(d.token)
              }
              else if (event === 'done') {
                _flush()
                messages.value.push({ role: 'assistant', content: d.answer, evidence: d.evidence, time: Date.now() })
                ans.value = ''
                ev.value = []
              }
            } catch { /* skip */ }
          }
        }
        buf = ''
      }
    } catch { /* ignore */ }
    streaming.value = false
  }
}
