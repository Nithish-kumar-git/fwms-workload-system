/**
 * Resolve the separately deployed synthetic-demo site for institutional builds.
 *
 * Returning null is intentional: an institutional frontend must never fall
 * back to posting a synthetic-demo login request to its own API origin.
 */
export function resolveDedicatedDemoDestination(value: string | undefined): string | null {
    if (!value) return null;

    try {
        const destination = new URL(value);
        if (destination.protocol !== 'https:' || destination.username || destination.password) {
            return null;
        }
        return destination.href;
    } catch {
        return null;
    }
}
