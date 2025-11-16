import React, { useRef, useState } from 'react'

type VideoPlayerProps = {
	src: string
	startAt?: number
	autoPlay?: boolean
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
	src,
	startAt = 0,
	autoPlay = true,
}) => {
	const videoRef = useRef<HTMLVideoElement | null>(null)
	const [hasSeeked, setHasSeeked] = useState(false)

	const handleLoadedMetadata = () => {
		const video = videoRef.current
		if (!video) return

		if (!hasSeeked && startAt > 0) {
			video.currentTime = startAt
			setHasSeeked(true)
		}

		if (autoPlay) {
			video.play().catch(err => {
				console.warn('Autoplay bị chặn:', err)
			})
		}
	}

	return (
		<video
			ref={videoRef}
			src={src}
			controls
			onLoadedMetadata={handleLoadedMetadata}
			style={{ width: '100%', height: '100%', backgroundColor: 'black' }}
		/>
	)
}
