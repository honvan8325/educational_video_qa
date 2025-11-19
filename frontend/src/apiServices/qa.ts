import httpService from '../services/http'
import type { QA } from '../types/qa'

export const QAApi = {
	askQuestion: ({
		question,
		videoIds,
		workspaceId,
		generatorType = 'gemini',
		retrieverType = 'vector',
		embeddingModel = 'dangvantuan',
		useReranker = false,
		useHistory = false,
		historyCount = 3,
	}: {
		workspaceId: string
		question: string
		videoIds: string[]
		retrieverType?: string
		generatorType?: string
		embeddingModel?: string
		useReranker?: boolean
		useHistory?: boolean
		historyCount?: number
	}): Promise<QA> => {
		return httpService.post(`/workspaces/${workspaceId}/ask`, {
			question,
			video_ids: videoIds,
			retriever_type: retrieverType,
			generator_type: generatorType,
			embedding_model: embeddingModel,
			use_reranker: useReranker,
			use_history: useHistory,
			history_count: historyCount,
		})
	},

	getHistory: (workspaceId: string): Promise<QA[]> => {
		return httpService.get(`/workspaces/${workspaceId}/history`)
	},

	deleteAllHistory: (workspaceId: string): Promise<void> => {
		return httpService.delete(`/workspaces/${workspaceId}/history`)
	},

	deleteQAItem: ({
		qaId,
		workspaceId,
	}: {
		workspaceId: string
		qaId: string
	}): Promise<void> => {
		return httpService.delete(`/workspaces/${workspaceId}/history/${qaId}`)
	},
}
