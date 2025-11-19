import { LogoutOutlined, SettingOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { Dropdown, Form, Modal, Select, Slider, Switch } from 'antd'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useLocalStorage } from 'usehooks-ts'
import { AuthApi } from '../apiServices/auth'

export function Header() {
	const [accessToken, setAccessToken] = useLocalStorage('access_token', '')
	const { data } = useQuery({
		queryFn: () => AuthApi.getMe(),
		queryKey: ['me', accessToken],
		enabled: !!accessToken,
	})

	const [openSettingModal, setOpenSettingModal] = useState(false)

	const [generatorType, setGeneratorType] = useLocalStorage(
		'generator_type',
		'gemini'
	)
	const [retrieverType, setRetrieverType] = useLocalStorage(
		'retriever_type',
		'vector'
	)
	const [embeddingModel, setEmbeddingModel] = useLocalStorage(
		'embedding_model',
		'halong'
	)
	const [useReranker, setUseReranker] = useLocalStorage('use_reranker', false)
	const [useHistory, setUseHistory] = useLocalStorage('use_history', true)
	const [historyCount, setUseHistoryCount] = useLocalStorage(
		'history_count',
		5
	)

	return (
		<>
			{openSettingModal && (
				<Modal
					title='Setting'
					open={openSettingModal}
					onCancel={() => setOpenSettingModal(false)}
					footer={null}
				>
					<Form layout='vertical' size='large'>
						<div className='flex gap-2'>
							<Form.Item
								label='Generator Type'
								className='flex-1'
							>
								<Select
									value={generatorType}
									onChange={value => setGeneratorType(value)}
									options={[
										{
											value: 'gemini',
											label: 'Gemini',
										},
									]}
								/>
							</Form.Item>

							<Form.Item
								label='Retriever Type'
								className='flex-1'
							>
								<Select
									value={retrieverType}
									onChange={value => setRetrieverType(value)}
									options={[
										{
											value: 'vector',
											label: 'Vector',
										},
										{
											value: 'bm25',
											label: 'BM25',
										},
										{
											value: 'hybrid',
											label: 'Hybrid',
										},
									]}
								/>
							</Form.Item>
						</div>

						{retrieverType !== 'bm25' && (
							<Form.Item label='Embedding Model'>
								<Select
									value={embeddingModel}
									onChange={value => setEmbeddingModel(value)}
									options={[
										{
											value: 'dangvantuan',
											label: 'dangvantuan/vietnamese-embedding',
										},
										{
											value: 'halong',
											label: 'hiieu/halong_embedding',
										},
									]}
								/>
							</Form.Item>
						)}

						<Form.Item label='Use Reranker'>
							<Switch
								checked={useReranker}
								onChange={checked => setUseReranker(checked)}
							/>
						</Form.Item>

						<div className='flex gap-2'>
							<Form.Item label='Use History' className='flex-1'>
								<Switch
									checked={useHistory}
									onChange={checked => setUseHistory(checked)}
								/>
							</Form.Item>

							{useHistory && (
								<Form.Item
									label='Use History Count'
									className='flex-2'
								>
									<Slider
										min={1}
										max={20}
										value={historyCount}
										onChange={value =>
											setUseHistoryCount(value as number)
										}
										marks={{
											1: '1',
											20: '20',
										}}
									/>
								</Form.Item>
							)}
						</div>
					</Form>
				</Modal>
			)}

			<header className='flex items-center justify-between h-16 px-4'>
				<Link to={'/'} className='flex items-center'>
					<span className='text-primary text-lg font-bold tracking-wider'>
						Video QA
					</span>
					<span className='text-gray-500 font-medium ml-4'>
						Team 5
					</span>
				</Link>

				<Dropdown
					trigger={['click']}
					menu={{
						items: [
							{
								key: 'setting',
								label: 'Setting',
								icon: <SettingOutlined />,
								onClick: () => {
									setOpenSettingModal(true)
								},
							},
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
		</>
	)
}
