import { Button, Form, Input, Modal, Typography } from 'antd'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLocalStorage } from 'usehooks-ts'
import { AuthApi } from '../apiServices/auth'
import { useCustomMutation } from '../hooks/useCustomMutation'

export function Login() {
	const [form] = Form.useForm()
	const [accessToken, setAccessToken] = useLocalStorage('access_token', '')
	const navigate = useNavigate()

	const { mutate, isPending } = useCustomMutation({
		mutationFn: AuthApi.login,
		onSuccess({ access_token }) {
			setAccessToken(access_token)
		},
		successMessage: 'Logged in successfully!',
	})

	useEffect(() => {
		if (accessToken) {
			navigate('/')
		}
	}, [accessToken, navigate])

	return (
		<div className='h-screen bg-gray-100'>
			<Modal
				open
				title={
					<Typography.Title level={3} className='m-0'>
						Log In
					</Typography.Title>
				}
				closable={false}
				mask={false}
				footer={
					<Button
						type='primary'
						loading={isPending}
						block
						size='large'
						onClick={() => {
							form.validateFields().then(values => {
								mutate(values)
							})
						}}
					>
						Log in
					</Button>
				}
			>
				<Form layout='vertical' size='large' form={form}>
					<Form.Item
						label='Username'
						name='username'
						rules={[
							{
								required: true,
								message: 'Please input your username!',
							},
							{
								pattern: /^\S+$/,
								message: 'Username cannot contain spaces!',
							},
						]}
					>
						<Input placeholder='Enter your username' />
					</Form.Item>
					<Form.Item
						label='Password'
						name='password'
						rules={[
							{
								required: true,
								message: 'Please input your password!',
							},
							{
								pattern: /^\S+$/,
								message: 'Password cannot contain spaces!',
							},
						]}
					>
						<Input.Password placeholder='Enter your password' />
					</Form.Item>
				</Form>
			</Modal>
		</div>
	)
}
