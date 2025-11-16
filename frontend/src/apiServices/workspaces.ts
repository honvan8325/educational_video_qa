import httpService from '../services/http'
import type { Workspace } from '../types/workspace'

export const WorkspacesApi = {
	getWorkspaces(): Promise<Workspace[]> {
		return httpService.get('/workspaces')
	},

	createWorkspace(name: string): Promise<Workspace> {
		return httpService.post('/workspaces', { name })
	},

	deleteWorkspace(workspaceId: string): Promise<void> {
		return httpService.delete(`/workspaces/${workspaceId}`)
	},

	updateWorkspace({
		workspaceId,
		name,
	}: {
		workspaceId: string
		name: string
	}): Promise<Workspace> {
		return httpService.put(`/workspaces/${workspaceId}`, { name })
	},

	getWorkspace(workspaceId: string): Promise<Workspace> {
		return httpService.get(`/workspaces/${workspaceId}`)
	},
}
