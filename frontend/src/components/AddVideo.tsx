import { InboxOutlined } from '@ant-design/icons'
import { useQueryClient } from '@tanstack/react-query'
import { Button, Form, Modal, Upload } from 'antd'
import { VideosApi } from '../apiServices/videos'
import { useCustomMutation } from '../hooks/useCustomMutation'
import { useLocalStorage } from 'usehooks-ts'

export function AddVideo({
	open,
	setOpen,
	workspaceId,
}: {
	open: boolean
	setOpen: (open: boolean) => void
	workspaceId: string
}) {
	const [form] = Form.useForm()
	const queryClient = useQueryClient()

	const [savedSelectedVideos, setSavedSelectedVideos] = useLocalStorage<
		string[] | undefined
	>(`selected_videos_${workspaceId}`, undefined, {
		serializer: value => JSON.stringify(value),
		deserializer: value => JSON.parse(value),
	})

	const { mutate, isPending } = useCustomMutation({
		mutationFn: VideosApi.uploadVideo,
		onSuccess(data) {
			queryClient.invalidateQueries({
				queryKey: ['videos', workspaceId],
			})

			if (savedSelectedVideos) {
				setSavedSelectedVideos([
					...savedSelectedVideos,
					data.id,
				])
			}

			setOpen(false)
		},
	})

	return (
		open && (
			<Modal
				title='Add Video'
				open={open}
				onCancel={() => setOpen(false)}
				confirmLoading={isPending}
				onOk={() => {
					form.validateFields().then(values => {
						const contextUnitsFile =
							values.context_units.fileList[0].originFileObj
						const videoFile =
							values.video_file.fileList[0].originFileObj

						contextUnitsFile.text().then((contextUnit: string) => {
							mutate({
								workspaceId: workspaceId,
								video: videoFile,
								contextUnits: JSON.parse(contextUnit),
							})
						})
					})
				}}
			>
				<Form layout='vertical' size='large' form={form}>
					<Form.Item
						label='Video'
						name='video_file'
						rules={[
							{
								required: true,
								message: 'Please upload a video file!',
							},
						]}
					>
						<Upload
							accept='video/*'
							beforeUpload={() => false}
							maxCount={1}
							style={{
								width: '100%',
							}}
						>
							<Button
								block
								icon={<InboxOutlined />}
								type='dashed'
							>
								Click to Upload
							</Button>
						</Upload>
					</Form.Item>

					<Form.Item
						help={
							<p>
								Get extracted features from{' '}
								<a
									href='https://www.kaggle.com/code/hngvnchng/notebookd084fefebd'
									target='_blank'
									rel='noreferrer'
									className='text-primary! underline!'
								>
									here
								</a>
							</p>
						}
						required
						label='Extracted features'
						name='context_units'
						rules={[
							{
								validator: async (_, value) => {
									if (
										!value ||
										value.fileList?.length === 0
									) {
										return Promise.reject(
											'Please upload a json file!'
										)
									}

									const file = value.fileList[0].originFileObj
									if (!file)
										return Promise.reject('Invalid file!')

									const text = await file.text()

									let json
									try {
										json = JSON.parse(text)
									} catch {
										return Promise.reject(
											'File is not a valid JSON!'
										)
									}

									if (!Array.isArray(json)) {
										return Promise.reject(
											'JSON must be an array!'
										)
									}

									const ok = json.every(
										item =>
											typeof item.text === 'string' &&
											typeof item.start_time ===
												'number' &&
											typeof item.end_time === 'number'
									)

									if (!ok) {
										return Promise.reject(
											'Each item must contain: text (string), start_time (number), end_time (number)'
										)
									}

									return Promise.resolve()
								},
							},
						]}
					>
						<Upload
							accept='application/json'
							beforeUpload={() => false}
							maxCount={1}
							style={{
								width: '100%',
							}}
						>
							<Button
								icon={<InboxOutlined />}
								type='dashed'
								block
							>
								Click to Upload
							</Button>
						</Upload>
					</Form.Item>
				</Form>
			</Modal>
		)
	)
}
