import type { ContextUnit } from './contextUnit'

export interface QA {
	id: string
	workspace_id: string
	question: string
	answer: string
	source_contexts: ContextUnit[]
	created_at: string
}
