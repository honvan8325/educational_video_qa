import httpService from '../services/http'
import type { User } from '../types/user'

export const AuthApi = {
	login({
		username,
		password,
	}: {
		username: string
		password: string
	}): Promise<{ access_token: string }> {
		return httpService.post('/auth/login', {
			username,
			password,
		})
	},

	getMe(): Promise<User> {
		return httpService.get('/auth/me')
	},
}
