import {
	DeleteOutlined,
	EditOutlined,
	EllipsisOutlined,
} from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Dropdown, List } from 'antd'
import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { WorkspacesApi } from '../apiServices/workspaces'
import { useCustomMutation } from '../hooks/useCustomMutation'
import type { Workspace } from '../types/workspace'
import { CreateWorkspace } from './CreateWorkspace'

export function WorkspaceList() {
	const { data, isLoading } = useQuery({
		queryFn: () => WorkspacesApi.getWorkspaces(),
		queryKey: ['workspaces'],
	})
	const [openCreateWorkspaceModal, setOpenCreateWorkspaceModal] =
		useState<Workspace>()

	const navigate = useNavigate()

	const queryClient = useQueryClient()
	const { mutate: update, isPending: isUpdating } = useCustomMutation({
		mutationFn: WorkspacesApi.updateWorkspace,
		onSuccess(data) {
			queryClient.invalidateQueries({
				queryKey: ['workspaces'],
			})
			navigate(`/${data.id}`)
			setOpenCreateWorkspaceModal(undefined)
		},
		successMessage: 'Workspace updated successfully!',
	})

	const { mutate: deleteWorkspace } = useCustomMutation({
		mutationFn: WorkspacesApi.deleteWorkspace,
		onSuccess() {
			navigate('/')
		},
		successMessage: 'Workspace deleted successfully!',
	})

	return (
		<>
			<CreateWorkspace
				open={openCreateWorkspaceModal !== undefined}
				setOpen={isOpen => {
					if (!isOpen) {
						setOpenCreateWorkspaceModal(undefined)
					}
				}}
				onSubmit={name => {
					if (!openCreateWorkspaceModal) return
					update({ workspaceId: openCreateWorkspaceModal.id, name })
				}}
				isPending={isUpdating}
				initialValues={{ name: openCreateWorkspaceModal?.name }}
			/>

			<List
				size='small'
				dataSource={data}
				loading={isLoading}
				bordered
				className='overflow-auto'
				renderItem={item => (
					<List.Item
						extra={
							<Dropdown
								trigger={['click']}
								menu={{
									items: [
										{
											key: '1',
											label: 'Update',
											icon: <EditOutlined />,
											onClick: () => {
												setOpenCreateWorkspaceModal(
													item
												)
											},
										},
										{
											key: '2',
											label: 'Delete',
											icon: <DeleteOutlined />,
											danger: true,
											onClick() {
												deleteWorkspace(item.id, {
													onSuccess() {
														queryClient.invalidateQueries(
															{
																queryKey: [
																	'workspaces',
																],
															}
														)
													},
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
						}
					>
						<List.Item.Meta
							title={
								<NavLink
									to={`/${item.id}`}
									className={({ isActive }) =>
										`${
											isActive &&
											'text-primary! font-medium'
										} block`
									}
								>
									{item.name}
								</NavLink>
							}
						/>
					</List.Item>
				)}
			/>
		</>
	)
}
