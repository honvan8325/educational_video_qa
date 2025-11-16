import { useQuery } from '@tanstack/react-query'
import { useLocalStorage } from 'usehooks-ts'
import { AuthApi } from '../apiServices/auth'
import { Dropdown } from 'antd'
import { LogoutOutlined } from '@ant-design/icons'
import { Link } from 'react-router-dom'

export function Header() {
	const [accessToken, setAccessToken] = useLocalStorage('access_token', '')
	const { data } = useQuery({
		queryFn: () => AuthApi.getMe(),
		queryKey: ['me', accessToken],
		enabled: !!accessToken,
	})

	return (
		<header className='flex items-center justify-between h-16 px-4'>
			<Link to={'/'} className='flex items-center'>
				<span className='text-primary text-lg font-bold tracking-wider'>
					Video QA
				</span>
				<span className='text-gray-500 font-medium ml-4'>Team 10</span>
			</Link>

			<Dropdown
				trigger={['click']}
				menu={{
					items: [
						{
							key: 'logout',
							label: 'Log out',
							onClick: () => {
								setAccessToken('')
							},
							icon: <LogoutOutlined />,
						},
					],
				}}
			>
				<span className='cursor-pointer'>{data?.username}</span>
			</Dropdown>
		</header>
	)
}
