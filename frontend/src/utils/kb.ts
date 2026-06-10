/** 知识库列表缓存，跨页面共享 */
let _cache: any[] | null = null

export async function getKBList(): Promise<any[]> {
  if (_cache) return _cache
  const r = await (await fetch('/api/knowledge-bases')).json()
  _cache = r.knowledge_bases || []
  return _cache
}

export function clearKBCache() { _cache = null }
