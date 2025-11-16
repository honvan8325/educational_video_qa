import axios from 'axios'

const httpService = axios.create({
	baseURL:
		import.meta.env.VITE_API_BASE_URL + '/api' ||
		'http://localhost:8000/api',
})

httpService.interceptors.request.use(config => {
	const accessToken = localStorage.getItem('access_token')
	if (accessToken) {
		config.headers.Authorization = `Bearer ${JSON.parse(accessToken)}`
	}

	return config
})

httpService.interceptors.response.use(
	response => response.data,
	error => {
		if (error.status === 401) {
			localStorage.removeItem('access_token')
		}

		if (
			error.response &&
			error.response.data &&
			error.response.data.detail
		) {
			if (typeof error.response.data.detail === 'string') {
				return Promise.reject(new Error(error.response.data.detail))
			} else if (Array.isArray(error.response.data.detail)) {
				const messages = error.response.data.detail
					.map((d: { msg: string }) => d.msg)
					.join(', ')
				return Promise.reject(new Error(messages))
			}
		}

		return Promise.reject(error)
	}
)

export default httpService
