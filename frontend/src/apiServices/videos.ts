import httpService from '../services/http'
import type { ContextUnit } from '../types/contextUnit'
import type { Video } from '../types/video'

export const VideosApi = {
	uploadVideo: ({
		contextUnits,
		video,
		workspaceId,
	}: {
		workspaceId: string
		video: File
		contextUnits: ContextUnit[]
	}): Promise<Video> => {
		const formData = new FormData()
		formData.append('video_file', video)
		formData.append('context_units', JSON.stringify(contextUnits))

		return httpService.post(
			'/workspaces/' + workspaceId + '/videos',
			formData,
			{
				headers: {
					'Content-Type': 'multipart/form-data',
				},
			}
		)
	},

	getVideos: (workspaceId: string): Promise<Video[]> => {
		return httpService.get('/workspaces/' + workspaceId + '/videos')
	},

	deleteVideo: ({
		workspaceId,
		videoId,
	}: {
		workspaceId: string
		videoId: string
	}): Promise<void> => {
		return httpService.delete(
			'/workspaces/' + workspaceId + '/videos/' + videoId
		)
	},
}
