import httpService from '../services/http'
import type { QA } from '../types/qa'

export const QAApi = {
	askQuestion: ({
		question,
		videoIds,
		workspaceId,
	}: {
		workspaceId: string
		question: string
		videoIds: string[]
	}): Promise<QA> => {
		return httpService.post(`/workspaces/${workspaceId}/ask`, {
			question,
			video_ids: videoIds,
		})
	},

	getHistory: (workspaceId: string): Promise<QA[]> => {
		return httpService.get(`/workspaces/${workspaceId}/history`)
	},
}
