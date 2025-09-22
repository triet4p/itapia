/**
 * Navigation Guards
 * 
 * Implements route protection logic for the application.
 * Contains middleware that runs before each navigation to check
 * authentication status and route permissions.
 */

import type { Router } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';

// List of routes that require authentication
const protectedRoutes = ['/profiles', '/advisor/[ticker]'];

/**
 * Sets up navigation guards for the router.
 * 
 * @param router - The Vue Router instance to attach guards to
 */
export function setupNavigationGuards(router: Router) {
    router.beforeEach((to, from, next) => {
        const authStore = useAuthStore();
        const isLoggedIn = authStore.isLoggedIn;

        const requiresAuth = protectedRoutes.some(path => to.path.startsWith(path));

        // Rule 1: Attempting to access a protected route while not logged in
        if (requiresAuth && !isLoggedIn) {
            // Redirect to login page
            next({ name: '/login' });
        }
        // Rule 2: Attempting to access login page while already logged in
        else if (to.path == '/login' && isLoggedIn) {
            // Redirect to home page
            next({ name: '/' });
        } 
        // Rule 3: Allow navigation to proceed
        else {
            next();
        }
    });
}