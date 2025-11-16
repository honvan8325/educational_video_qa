import { useMutation, type UseMutationOptions } from '@tanstack/react-query'
import { useMessageStore } from '../stores/useMessageStore'

interface CustomMutationOptions<
	TData = unknown,
	TError = Error,
	TVariables = void,
	TContext = unknown
> extends UseMutationOptions<TData, TError, TVariables, TContext> {
	successMessage?: string
}

export function useCustomMutation<
	TData = unknown,
	TError = Error,
	TVariables = void,
	TContext = unknown
>(options: CustomMutationOptions<TData, TError, TVariables, TContext>) {
	const messageApi = useMessageStore(s => s.messageApi)

	return useMutation<TData, TError, TVariables, TContext>({
		retry: false,
		...options,

		async onSuccess(data, variables, onMutateResult, context) {
			if (options.successMessage) {
				messageApi?.success(options.successMessage)
			}
			options.onSuccess?.(data, variables, onMutateResult, context)
		},

		async onError(error, variables, onMutateResult, context) {
			if (error instanceof Error) {
				messageApi?.error(error.message || 'An error occurred.')
			} else {
				messageApi?.error('An unknown error occurred.')
			}

			options.onError?.(error, variables, onMutateResult, context)
		},
	})
}
