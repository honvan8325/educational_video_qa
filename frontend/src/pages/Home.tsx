import { PlusOutlined, YoutubeOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Card, Empty } from 'antd'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useLocalStorage } from 'usehooks-ts'
import { WorkspacesApi } from '../apiServices/workspaces'
import { AddVideo } from '../components/AddVideo'
import { CreateWorkspace } from '../components/CreateWorkspace'
import { Header } from '../components/Header'
import { QA } from '../components/QA'
import { VideoList } from '../components/VideoList'
import { WorkspaceList } from '../components/WorkspaceList'
import { useCustomMutation } from '../hooks/useCustomMutation'

export function Home() {
	const [accessToken] = useLocalStorage('access_token', '')
	const navigate = useNavigate()

	const params = useParams<{ id?: string }>()
	const workspaceId = params.id

	const [openCreateWorkspaceModal, setOpenCreateWorkspaceModal] =
		useState(false)
	const [openAddVideoModal, setOpenAddVideoModal] = useState(false)

	useEffect(() => {
		if (!accessToken) {
			navigate('/login')
		}
	}, [accessToken, navigate])

	const queryClient = useQueryClient()
	const { mutate, isPending } = useCustomMutation({
		mutationFn: WorkspacesApi.createWorkspace,
		onSuccess(data) {
			queryClient.invalidateQueries({
				queryKey: ['workspaces'],
			})
			navigate(`/${data.id}`)
			setOpenCreateWorkspaceModal(false)
		},
		successMessage: 'Workspace created successfully!',
	})

	const [selectedVideos, setSelectedVideos] = useState<string[]>([])

	const { data: workspace } = useQuery({
		queryKey: ['workspace', workspaceId],
		queryFn: () => WorkspacesApi.getWorkspace(workspaceId!),
		enabled: !!workspaceId,
	})

	return (
		<>
			{openCreateWorkspaceModal && (
				<CreateWorkspace
					open={openCreateWorkspaceModal}
					setOpen={setOpenCreateWorkspaceModal}
					onSubmit={mutate}
					isPending={isPending}
				/>
			)}
			{workspaceId && (
				<AddVideo
					open={openAddVideoModal}
					setOpen={setOpenAddVideoModal}
					workspaceId={workspaceId}
				/>
			)}

			<div className='h-screen flex flex-col bg-gray-100 overflow-hidden'>
				<Header />

				<div className='grid grid-cols-24 px-4 gap-5 flex-1 pb-4 min-h-0 h-full'>
					<Card
						className='col-span-5 min-h-0 flex flex-col h-full'
						title='Workspaces'
						size='small'
						classNames={{
							body: 'flex-1 overflow-hidden flex flex-col min-h-0',
						}}
					>
						<Button
							className='mb-4'
							type='primary'
							block
							icon={<PlusOutlined />}
							onClick={() => setOpenCreateWorkspaceModal(true)}
						>
							Create Workspace
						</Button>

						<WorkspaceList />
					</Card>

					<Card
						size='small'
						className='col-span-12 flex flex-col min-h-0 h-full'
						title={workspaceId && workspace && workspace.name}
						classNames={{
							body: 'flex-1 overflow-hidden min-h-0 flex flex-col',
						}}
					>
						{workspaceId ? (
							<QA
								selectedVideos={selectedVideos}
								workspaceId={workspaceId}
							/>
						) : (
							<Empty description='Create or select a workspace to get started!' />
						)}
					</Card>

					<Card
						size='small'
						title='Sources'
						className='col-span-7 min-h-0 flex flex-col h-full'
						classNames={{
							body: 'flex-1 flex flex-col overflow-hidden min-h-0',
						}}
					>
						{workspaceId ? (
							<>
								<Button
									className='mb-4'
									block
									icon={<YoutubeOutlined />}
									onClick={() => setOpenAddVideoModal(true)}
								>
									Add Video
								</Button>

								<VideoList
									workspaceId={workspaceId}
									selectedVideos={selectedVideos}
									onSelectedVideosChange={setSelectedVideos}
								/>
							</>
						) : (
							<Empty description='Create or select a workspace to get started!' />
						)}
					</Card>
				</div>
			</div>
		</>
	)
}
