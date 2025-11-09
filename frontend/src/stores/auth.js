import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

// Create a single axios instance so we can attach interceptors for token refresh
const api = axios.create({ baseURL: API_BASE })

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('fm_token') || null,
        email: localStorage.getItem('fm_email') || null,
        loading: false,
        error: null,
    }),
    getters: {
        isAuthenticated: (state) => !!state.token,
        authHeaders: (state) => state.token ? { Authorization: `Bearer ${state.token}` } : {},
    },
    actions: {
        _attachInterceptorsOnce() {
            if (this._interceptorsAttached) return
            // Request: inject Authorization header
            api.interceptors.request.use(cfg => {
                if (this.token) {
                    cfg.headers.Authorization = `Bearer ${this.token}`
                }
                return cfg
            })
            // Response: check for refreshed token header
            api.interceptors.response.use(res => {
                const newToken = res.headers['x-new-token'] || res.headers['X-New-Token']
                if (newToken && newToken !== this.token) {
                    this.token = newToken
                    localStorage.setItem('fm_token', newToken)
                }
                return res
            }, err => {
                // Optional: auto-logout on 401 token expired (detail === 'Token expired')
                if (err.response?.status === 401) {
                    const detail = err.response?.data?.detail
                    if (detail === 'Token expired') {
                        this.logout()
                    }
                }
                return Promise.reject(err)
            })
            this._interceptorsAttached = true
        },
        async login(email, password) {
            this.loading = true
            this.error = null
            try {
                this._attachInterceptorsOnce()
                const r = await api.post(`/auth/login`, { email, password })
                this.token = r.data.access_token
                this.email = email
                localStorage.setItem('fm_token', this.token)
                localStorage.setItem('fm_email', this.email)
            } catch (e) {
                this.error = e.response?.data?.detail || e.message
                throw e
            } finally {
                this.loading = false
            }
        },
        async register(email, password) {
            this.loading = true
            this.error = null
            try {
                this._attachInterceptorsOnce()
                await api.post(`/auth/register`, { email, password })
                await this.login(email, password)
            } catch (e) {
                this.error = e.response?.data?.detail || e.message
                throw e
            } finally {
                this.loading = false
            }
        },
        logout() {
            this.token = null
            this.email = null
            localStorage.removeItem('fm_token')
            localStorage.removeItem('fm_email')
        }
    }
})

// Ensure interceptors attach early if a token already exists on page load
const preAuthStore = useAuthStore()
if (preAuthStore.token) {
    preAuthStore._attachInterceptorsOnce()
}
