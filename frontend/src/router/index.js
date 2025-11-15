import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const Login = () => import('../views/Login.vue')
const Register = () => import('../views/Register.vue')
const Dashboard = () => import('../views/Dashboard.vue')
const Purchases = () => import('../views/Purchases.vue')
const Sales = () => import('../views/Sales.vue')
const Customers = () => import('../views/Customers.vue')
const Settings = () => import('../views/Settings.vue')

const routes = [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', component: Login },
    { path: '/register', component: Register },
    { path: '/dashboard', component: Dashboard, meta: { requiresAuth: true } },
    { path: '/purchases', component: Purchases, meta: { requiresAuth: true } },
    { path: '/sales', component: Sales, meta: { requiresAuth: true } },
    { path: '/customers', component: Customers, meta: { requiresAuth: true } },
    { path: '/settings', component: Settings, meta: { requiresAuth: true } },
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, _from, next) => {
    const auth = useAuthStore()
    if (to.meta.requiresAuth && !auth.isAuthenticated) {
        next('/login')
    } else if ((to.path === '/login' || to.path === '/register') && auth.isAuthenticated) {
        next('/dashboard')
    } else {
        next()
    }
})

export default router
