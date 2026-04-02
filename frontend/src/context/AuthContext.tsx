import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { getCurrentUser } from '../api/client';

interface User {
    staff_id: number;
    email: string;
    name: string;
    role: string;  // 'faculty' | 'tt_coordinator' | 'hod'
    is_class_teacher?: boolean;
    ct_program?: string;
    ct_section?: string;
    ct_semester?: string;
    ct_shift?: string;
    ct_curriculum_year?: string;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    isFaculty: boolean;
    isCoordinator: boolean;
    isHOD: boolean;
    setUser: (user: User | null) => void;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    loading: true,
    isFaculty: false,
    isCoordinator: false,
    isHOD: false,
    setUser: () => {},
    refreshUser: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    const refreshUser = async () => {
        const token = localStorage.getItem('jwt_token');
        if (!token) {
            setUser(null);
            setLoading(false);
            return;
        }
        try {
            const res = await getCurrentUser();
            console.log('AUTH: user from /auth/me →', res.data);
            console.log('USER ROLE:', res.data.role);
            setUser(res.data);
        } catch {
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refreshUser();
    }, []);

    // All flags derived from user.role ONLY
    const isHOD = user?.role === 'hod';
    const isCoordinator = user?.role === 'tt_coordinator' || isHOD;
    const isFaculty = user?.role === 'faculty';

    return (
        <AuthContext.Provider value={{ user, loading, isFaculty, isCoordinator, isHOD, setUser, refreshUser }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}
