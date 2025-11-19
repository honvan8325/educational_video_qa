import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider, message } from 'antd'
import { useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import { Home } from './pages/Home'
import { Login } from './pages/Login'
import { WatchPage } from './pages/Watch'
import { useMessageStore } from './stores/useMessageStore'

const queryClient = new QueryClient({
	defaultOptions: {
		queries: {
			retry: false,
			refetchOnWindowFocus: false,
			staleTime: 3 * 60 * 1000, // 3 minutes
		},
	},
})

function App() {
	const setMessageApi = useMessageStore(s => s.setMessageApi)
	const [messageApi, contextHolder] = message.useMessage()

	useEffect(() => {
		setMessageApi(messageApi)
	}, [messageApi, setMessageApi])

	const location = useLocation()

	const state = location.state as { backgroundLocation?: Location }

	return (
		<ConfigProvider
			theme={{
				token: {
					colorPrimary: '#615fff',
					fontFamily: "'Open Sans', sans-serif",
				},
			}}
		>
			<QueryClientProvider client={queryClient}>
				{contextHolder}

				{state?.backgroundLocation && (
					<Routes>
						<Route path='/watch' element={<WatchPage />} />
					</Routes>
				)}

				<Routes location={state?.backgroundLocation || location}>
					<Route path='/' element={<Home />} />
					<Route path='/login' element={<Login />} />
					<Route path='/:id' element={<Home />} />
				</Routes>
			</QueryClientProvider>
		</ConfigProvider>
	)
}

export default App
