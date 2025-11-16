import { DeleteOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Checkbox, List } from 'antd'
import { useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useLocalStorage } from 'usehooks-ts'
import { VideosApi } from '../apiServices/videos'
import { useCustomMutation } from '../hooks/useCustomMutation'

export function VideoList({
	workspaceId,
	onSelectedVideosChange,
	selectedVideos,
}: {
	workspaceId: string
	selectedVideos: string[]
	onSelectedVideosChange: (selectedVideos: string[]) => void
}) {
	const { data, isLoading } = useQuery({
		queryFn: () => VideosApi.getVideos(workspaceId),
		queryKey: ['videos', workspaceId],
	})

	const [savedSelectedVideos, setSavedSelectedVideos] = useLocalStorage<
		string[] | undefined
	>(`selected_videos_${workspaceId}`, undefined, {
		serializer: value => JSON.stringify(value),
		deserializer: value => JSON.parse(value),
	})

	useEffect(() => {
		if (savedSelectedVideos == undefined && data) {
			onSelectedVideosChange(data.map(video => video.id))
		} else if (savedSelectedVideos) {
			onSelectedVideosChange(savedSelectedVideos)
		}
	}, [data, onSelectedVideosChange, savedSelectedVideos])

	const location = useLocation()

	const queryClient = useQueryClient()

	const { mutate } = useCustomMutation({
		mutationFn: VideosApi.deleteVideo,
		successMessage: 'Video deleted successfully!',
		onSuccess(_, mutationVariables) {
			queryClient.invalidateQueries({
				queryKey: ['videos', workspaceId],
			})
			setSavedSelectedVideos(
				savedSelectedVideos?.filter(
					id => id !== mutationVariables.videoId
				)
			)
		},
	})

	return (
		<div className='flex flex-col overflow-hidden min-h-0'>
			<div className='mb-3'>
				<Checkbox
					disabled={isLoading || !data || data.length === 0}
					onChange={e => {
						if (!data) return
						if (e.target.checked) {
							const allVideoIds = data.map(video => video.id)

							setSavedSelectedVideos(allVideoIds)
						} else {
							setSavedSelectedVideos([])
						}
					}}
					checked={
						selectedVideos.length === data?.length ? true : false
					}
				>
					Select All
				</Checkbox>
			</div>

			<List
				bordered
				loading={isLoading}
				dataSource={data}
				className='flex-1 overflow-auto'
				renderItem={item => (
					<List.Item
						extra={
							<Link
								to={`/watch?url=${encodeURIComponent(
									`${
										import.meta.env.VITE_API_BASE_URL
									}/static/videos/${item.file_path
										.split('/')
										.slice(2, 4)
										.join('/')}`
								)}&title=${encodeURIComponent(item.filename)}`}
								state={{
									backgroundLocation: location,
								}}
								className='relative w-12 aspect-square rounded-lg overflow-hidden  cursor-pointer'
							>
								<img
									className='object-center object-cover w-full h-full'
									src={`${
										import.meta.env.VITE_API_BASE_URL
									}/static/thumbnails/${item.thumbnail_path
										.split('/')
										.slice(2, 4)
										.join('/')}`}
								/>
								<div className='bg-black/30 flex items-center w-full h-full absolute inset-0 justify-center text-white'>
									<PlayCircleOutlined className='text-lg' />
								</div>
							</Link>
						}
						actions={[
							<Button
								key={'delete'}
								icon={<DeleteOutlined />}
								size='small'
								danger
								type='text'
								onClick={() => {
									mutate({
										workspaceId,
										videoId: item.id,
									})
								}}
							/>,
						]}
					>
						<List.Item.Meta
							avatar={
								<Checkbox
									checked={selectedVideos.some(
										id => id === item.id
									)}
									onChange={e => {
										if (e.target.checked) {
											setSavedSelectedVideos([
												...selectedVideos,
												item.id,
											])
										} else {
											setSavedSelectedVideos(
												selectedVideos.filter(
													id => id !== item.id
												)
											)
										}
									}}
								/>
							}
							title={
								<span className='line-clamp-2'>
									{item.filename}
								</span>
							}
							description={
								<p>
									{Math.floor(item.duration / 60)
										.toString()
										.padStart(2, '0')}
									:
									{Math.floor(item.duration % 60)
										.toString()
										.padStart(2, '0')}
									{' | '}
									{(item.file_size / (1024 * 1024)).toFixed(
										2
									)}{' '}
									MB
								</p>
							}
						/>
					</List.Item>
				)}
			/>
		</div>
	)
}
