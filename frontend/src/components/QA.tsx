import {
	ArrowRightOutlined,
	CopyOutlined,
	DeleteOutlined,
	EllipsisOutlined,
} from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
	Button,
	Card,
	Dropdown,
	Empty,
	Input,
	Spin,
	Tag,
	Typography,
} from 'antd'
import MarkdownIt from 'markdown-it'
import mk from 'markdown-it-katex'
import type StateInline from 'markdown-it/lib/rules_inline/state_inline.mjs'
import type Token from 'markdown-it/lib/token.mjs'
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useLocalStorage } from 'usehooks-ts'
import { QAApi } from '../apiServices/qa'
import { useCustomMutation } from '../hooks/useCustomMutation'
import { useMessageStore } from '../stores/useMessageStore'

function citationPlugin(md: MarkdownIt) {
	md.inline.ruler.after(
		'text',
		'citation',
		(state: StateInline, silent: boolean): boolean => {
			const start = state.pos
			const max = state.posMax

			if (start >= max) return false
			if (state.src[start] !== '[') return false

			const match = state.src.slice(start).match(/^\[(\d+)\]/)
			if (!match) return false

			if (!silent) {
				const open: Token = state.push('citation_open', 'span', 1)
				open.attrs = [
					[
						'class',
						'text-primary font-medium cursor-pointer mx-[1px]',
					],
				]

				const text: Token = state.push('text', '', 0)
				text.content = match[0]

				state.push('citation_close', 'span', -1)
			}

			state.pos = start + match[0].length

			return true
		}
	)
}

const md = new MarkdownIt({
	html: false,
	linkify: true,
	breaks: true,
})
	.use(mk)
	.use(citationPlugin)

export function QA({
	selectedVideos,
	workspaceId,
}: {
	selectedVideos: string[]
	workspaceId: string
}) {
	const [question, setQuestion] = useState('')
	const [placeholder, setPlaceholder] = useState('')

	const { data, isLoading, isSuccess } = useQuery({
		queryKey: ['qa', workspaceId],
		queryFn: () => QAApi.getHistory(workspaceId),
	})

	const navigate = useNavigate()
	const location = useLocation()

	const queryClient = useQueryClient()

	const { mutate, isPending } = useCustomMutation({
		mutationFn: QAApi.askQuestion,
		onSuccess() {
			setPlaceholder('')
			queryClient.invalidateQueries({
				queryKey: ['qa', workspaceId],
			})

			queryClient.invalidateQueries({
				queryKey: ['workspaces'],
			})
		},
		onError() {
			setPlaceholder('')
		},
	})

	const { mutate: deleteQAItem } = useCustomMutation({
		mutationFn: QAApi.deleteQAItem,
		onSuccess() {
			queryClient.invalidateQueries({
				queryKey: ['qa', workspaceId],
			})
		},
		successMessage: 'QA item deleted successfully!',
	})

	const [generatorType] = useLocalStorage<string>('generator_type', 'gemini')
	const [retrieverType] = useLocalStorage<string>('retriever_type', 'vector')
	const [embeddingModel] = useLocalStorage<string>(
		'embedding_model',
		'dangvantuan'
	)
	const [useReranker] = useLocalStorage<boolean>('use_reranker', false)
	const [useHistory] = useLocalStorage<boolean>('use_history', true)
	const [historyCount] = useLocalStorage<number>('history_count', 5)

	const messageApi = useMessageStore(s => s.messageApi)

	return (
		<div className='flex flex-col flex-1 min-h-0'>
			<div className='flex-1 overflow-y-auto min-h-0 flex flex-col justify-end py-4 -mx-4 px-4'>
				{isSuccess && data.length == 0 && !placeholder && (
					<Empty description='Ask a question to get started!' />
				)}

				{isLoading && (
					<div className='flex justify-center'>
						<Spin spinning />
					</div>
				)}

				{data &&
					data.length > 0 &&
					data.map(qa => (
						<div key={qa.id} className='w-full flex flex-col mb-12'>
							<div className='max-w-10/12 self-end bg-primary text-white px-6 py-4 rounded-2xl mb-2'>
								{qa.question}
							</div>

							<div className='flex self-end mb-4 items-center gap-1'>
								<Button
									size='small'
									type='text'
									icon={<CopyOutlined />}
									onClick={() => {
										navigator.clipboard.writeText(
											qa.question
										)
										messageApi?.success(
											'Text copied to clipboard!'
										)
									}}
								/>

								<Dropdown
									trigger={['click']}
									menu={{
										items: [
											{
												key: 'delete',
												label: 'Delete',
												danger: true,
												icon: <DeleteOutlined />,
												onClick: () => {
													deleteQAItem({
														workspaceId,
														qaId: qa.id,
													})
												},
											},
										],
									}}
								>
									<Button
										size='small'
										type='text'
										icon={<EllipsisOutlined />}
									/>
								</Dropdown>
							</div>

							<Card
								className='max-w-10/12 self-start mb-2!'
								size='small'
							>
								{typeof qa.response_time === 'number' && (
									<div className='text-xs text-gray-500 mb-1 flex justify-end'>
										{qa.response_time.toFixed(2)}s
									</div>
								)}

								<div
									className='prose prose-sm max-w-none!'
									dangerouslySetInnerHTML={{
										__html: md.render(qa.answer),
									}}
								/>

								{qa.source_contexts.filter((_, index) =>
									qa.answer.includes(`[${index + 1}]`)
								).length > 0 && (
									<div className='mt-4'>
										<Card
											size='small'
											className='flex items-center flex-wrap'
										>
											{qa.source_contexts
												.map((context, index) => ({
													context,
													originalIndex: index,
												}))
												.filter(({ originalIndex }) =>
													qa.answer.includes(
														`[${originalIndex + 1}]`
													)
												)
												.map(
													({
														context,
														originalIndex,
													}) => (
														<Tag
															key={context.id}
															icon={
																<span className='font-medium mr-1 text-primary'>
																	[
																	{originalIndex +
																		1}
																	]
																</span>
															}
															onClick={() => {
																navigate(
																	`/watch?url=${encodeURIComponent(
																		`${
																			import.meta
																				.env
																				.VITE_API_BASE_URL
																		}/static/videos/${context.video_path
																			.split(
																				'/'
																			)
																			.slice(
																				2,
																				4
																			)
																			.join(
																				'/'
																			)}`
																	)}&title=${encodeURIComponent(
																		context.video_path
																			.split(
																				'/'
																			)
																			.pop()!
																	)}&start_time=${
																		context.start_time
																	}`,
																	{
																		state: {
																			backgroundLocation:
																				location,
																		},
																	}
																)
															}}
															className='cursor-pointer'
														>
															{context.video_path
																.split('/')
																.pop()!
																.slice(0, 10) +
																(context.video_path
																	.split('/')
																	.pop()!
																	.length! >
																10
																	? '...'
																	: '')}{' '}
															(
															{Math.floor(
																context.start_time /
																	60
															)
																.toString()
																.padStart(
																	2,
																	'0'
																)}
															:
															{Math.floor(
																context.start_time %
																	60
															)
																.toString()
																.padStart(
																	2,
																	'0'
																)}
															{' - '}
															{Math.floor(
																context.end_time /
																	60
															)
																.toString()
																.padStart(
																	2,
																	'0'
																)}
															:
															{Math.floor(
																context.end_time %
																	60
															)
																.toString()
																.padStart(
																	2,
																	'0'
																)}
															)
														</Tag>
													)
												)}
										</Card>
									</div>
								)}
							</Card>

							<div className='flex self-start items-center'>
								<Button
									className='self-start'
									size='small'
									type='text'
									icon={<CopyOutlined />}
									onClick={() => {
										navigator.clipboard.writeText(
											qa.answer.replace(/\[(\d+)\]/g, '')
										)
										messageApi?.success(
											'Text copied to clipboard!'
										)
									}}
								/>

								<Dropdown
									trigger={['click']}
									menu={{
										items: [
											{
												key: 'delete',
												label: 'Delete',
												danger: true,
												icon: <DeleteOutlined />,
												onClick: () => {
													deleteQAItem({
														workspaceId,
														qaId: qa.id,
													})
												},
											},
										],
									}}
								>
									<Button
										size='small'
										type='text'
										icon={<EllipsisOutlined />}
									/>
								</Dropdown>
							</div>
						</div>
					))}

				{placeholder && (
					<div className='w-full flex flex-col mb-12'>
						<div className='max-w-10/12 self-end bg-primary text-white px-6 py-4 rounded-2xl mb-4'>
							{placeholder}
						</div>

						<Card
							className='max-w-10/12 self-start min-w-32 flex justify-center'
							size='small'
						>
							<Spin spinning size='small' />
						</Card>
					</div>
				)}
			</div>

			<Card size='small' className='shrink-0'>
				<div className='flex items-start gap-2'>
					<Input.TextArea
						className='flex-1'
						size='large'
						allowClear
						autoSize={{ minRows: 1, maxRows: 6 }}
						placeholder='Ask a question about the videos...'
						value={question}
						onChange={e => setQuestion(e.target.value)}
						onKeyDown={e => {
							if (
								e.key === 'Enter' &&
								!e.shiftKey &&
								question.trim() &&
								selectedVideos.length > 0 &&
								!isPending
							) {
								e.preventDefault()
								setPlaceholder(question.trim())
								mutate({
									workspaceId,
									question: question.trim(),
									videoIds: selectedVideos,
									generatorType,
									retrieverType,
									embeddingModel,
									useReranker,
									useHistory,
									historyCount,
								})
								setQuestion('')
							}
						}}
					/>

					<Button
						type='primary'
						size='large'
						icon={<ArrowRightOutlined />}
						disabled={
							!question.trim() ||
							selectedVideos.length === 0 ||
							isPending
						}
						loading={isPending}
						onClick={() => {
							setPlaceholder(question.trim())
							mutate({
								workspaceId,
								question: question.trim(),
								videoIds: selectedVideos,
								generatorType,
								retrieverType,
								embeddingModel,
								useReranker,
								useHistory,
								historyCount,
							})
							setQuestion('')
						}}
					></Button>
				</div>

				<div className='mt-2 flex items-center justify-between'>
					<Typography.Text type='secondary'>
						{selectedVideos.length} sources | {generatorType} |{' '}
						{retrieverType}
						{retrieverType !== 'bm25' && ' | ' + embeddingModel}
						{useReranker ? ' | Reranker enabled' : ''}
					</Typography.Text>

					<Typography.Text type='secondary'>
						{data && `${data.length} Q&A`}
					</Typography.Text>
				</div>
			</Card>
		</div>
	)
}
