export type ActionRunner = <T>(
  action: () => Promise<T>,
  successMessage: string,
) => Promise<T | undefined>
