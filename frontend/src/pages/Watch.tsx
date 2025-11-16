import { CloseOutlined } from '@ant-design/icons'
import { Button, Result } from 'antd'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { VideoPlayer } from '../components/VideoPlayer'

export function WatchPage() {
	const [searchParams] = useSearchParams()
	const url = decodeURIComponent(searchParams.get('url') || '')
	const title = decodeURIComponent(
		searchParams.get('title') || 'Video Player'
	)
	const startTimeParam = searchParams.get('start_time')

	const navigate = useNavigate()

	if (!url) {
		return (
			<Result
				status={'404'}
				title='404'
				subTitle='Sorry, the video URL is missing.'
			/>
		)
	}

	let startTime = startTimeParam ? parseFloat(startTimeParam) : 0
	if (isNaN(startTime)) {
		startTime = 0
	}

	return (
		<div
			className='fixed inset-0 bg-black/80 z-10 flex items-center justify-center'
			onClick={() => {
				navigate(-1)
			}}
		>
			<div
				className='w-[1000px] aspect-video'
				onClick={e => {
					e.stopPropagation()
				}}
			>
				<VideoPlayer src={url} startAt={startTime} />
			</div>

			<div className='absolute top-4 left-4 z-10 flex items-center'>
				<Button
					onClick={e => {
						e.stopPropagation()
						navigate(-1)
					}}
					size='large'
					icon={<CloseOutlined />}
					variant='text'
					color='primary'
				/>

				<span className='text-white text-lg ml-8 font-medium'>
					{title}
				</span>
			</div>
		</div>
	)
}
