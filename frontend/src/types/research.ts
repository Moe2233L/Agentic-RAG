export interface Evidence { id: string; text: string; source: string; score: number }
export interface Message { role: 'user' | 'assistant'; content: string; evidence?: Evidence[]; _evShow?: boolean }
