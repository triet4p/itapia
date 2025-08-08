import type { Router } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';

const protectedRoutes = ['/profiles']

export function setupNavigationGuards(router: Router) {
    router.beforeEach((to, from, next) => {
        const authStore = useAuthStore();
        const isLoggedIn = authStore.isLoggedIn;

        const requiresAuth = protectedRoutes.includes(to.path);

        //Quy tắc 1: Cố gắng truy cập vào trang được bảo vệ khi đang đăng nhập
        if (requiresAuth && !isLoggedIn) {
            //Điều hướng về trang đăng nhập
            next({ name: '/login' });
        }
        // Quy tắc 2: Cố gắng truy cập trang /login khi đã đăng nhập
        else if (to.path == '/login' && isLoggedIn) {
            //Điều về home page
            next({ name: '/' });
        } 
        // Quy tắc 3: Cho phép đi tiếp
        else {
            next();
        }
    });
}