import { Form, Input, Modal } from 'antd'
import { useEffect } from 'react'

export function CreateWorkspace({
	open,
	setOpen,
	onSubmit,
	isPending,
	initialValues,
}: {
	open: boolean
	setOpen: (open: boolean) => void
	onSubmit?: (name: string) => void
	isPending?: boolean
	initialValues?: { name?: string }
}) {
	const [form] = Form.useForm()

	useEffect(() => {
		if (initialValues) {
			form.setFieldsValue(initialValues)
		}
	}, [initialValues, form])

	return (
		<Modal
			title='Create Workspace'
			open={open}
			onCancel={() => setOpen(false)}
			confirmLoading={isPending}
			onOk={() => {
				form.validateFields().then(values => {
					onSubmit?.(values.name)
				})
			}}
		>
			<Form layout='vertical' size='large' form={form}>
				<Form.Item
					label='Workspace Name'
					name='name'
					rules={[
						{
							required: true,
							message: 'Please input the workspace name!',
						},
					]}
				>
					<Input placeholder='Enter workspace name' autoFocus />
				</Form.Item>
			</Form>
		</Modal>
	)
}
