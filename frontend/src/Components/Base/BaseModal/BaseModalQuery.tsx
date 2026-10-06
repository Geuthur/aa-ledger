// Third Party
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { QueryKey } from '@tanstack/react-query';
import Cookies from 'js-cookie';

type FormData = Record<string, string | boolean>;

function buildHeaders(): Record<string, string> {
    const csrf = Cookies.get('csrftoken');
    return csrf ? { 'X-CSRFToken': csrf } : {};
}

/** Mutation für Delete / Update / Bestätigungen (ohne Body) */
export function useApproveMutation(queryKey?: QueryKey | QueryKey[]) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (url: string) => {
            const response = await fetch(url, {
                method: 'POST',
                credentials: 'same-origin',
                headers: buildHeaders(),
            });

            const data = await response.json();

            if (!response.ok || data.success !== true) {
                throw new Error(data.message ?? 'Unknown error');
            }
            return data;
        },
        onSuccess: async () => {
            if (queryKey) {
                if (Array.isArray(queryKey) && Array.isArray(queryKey[0])) {
                    await Promise.all(
                        (queryKey as QueryKey[]).map((key) =>
                            queryClient.invalidateQueries({ queryKey: key, refetchType: 'all' })
                        )
                    );
                } else {
                    await queryClient.invalidateQueries({ queryKey: queryKey as QueryKey, refetchType: 'all' });
                }
            }
        },
    });
}

/** Mutation für Formulare (mit Formulardaten als URLSearchParams) */
export function useFormApproveMutation(queryKey?: QueryKey | QueryKey[]) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ url, formData = {} }: { url: string; formData?: FormData }) => {
            const body = new URLSearchParams();
            for (const [key, value] of Object.entries(formData)) {
                if (typeof value === 'boolean') {
                    if (value) body.append(key, 'on');
                } else {
                    body.append(key, value);
                }
            }

            const response = await fetch(url, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    ...buildHeaders(),
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: body.toString(),
            });

            const data = await response.json();

            if (!response.ok || data.success !== true) {
                throw new Error(data.message ?? 'Unknown error');
            }
            return data;
        },
        onSuccess: async () => {
            if (queryKey) {
                if (Array.isArray(queryKey) && Array.isArray(queryKey[0])) {
                    await Promise.all(
                        (queryKey as QueryKey[]).map((key) =>
                            queryClient.invalidateQueries({ queryKey: key, refetchType: 'all' })
                        )
                    );
                } else {
                    await queryClient.invalidateQueries({ queryKey: queryKey as QueryKey, refetchType: 'all' });
                }
            }
        },
    });
}
