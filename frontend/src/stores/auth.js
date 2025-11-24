import { defineStore } from 'pinia'
import axios from 'axios'
import JSEncrypt from 'jsencrypt'

const API_BASE = import.meta.env.VITE_API_BASE || ''

export const api = axios.create({ baseURL: API_BASE })
let interceptorsAttached = false

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('fm_token') || null,
        email: localStorage.getItem('fm_email') || null,
        loading: false,
        error: null,
        pubkeyPem: null,
    }),
    getters: {
        isAuthenticated: (state) => !!state.token,
        authHeaders: (state) => state.token ? { Authorization: `Bearer ${state.token}` } : {},
    },
    actions: {
        async ensureCrypto(forceRefresh = false) {
            if (this.pubkeyPem && !forceRefresh) return
            try {
                const r = await api.get('/auth/pubkey')
                this.pubkeyPem = r.data?.pem
            } catch (e) {
                // If fetching key fails, we'll fall back to plaintext
                console.error('Failed to fetch public key:', e)
                this.pubkeyPem = null
            }
        },
        ensureInterceptors() {
            if (interceptorsAttached) return
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
                    if (detail === 'Token expired' || detail === 'Could not validate credentials') {
                        this.logout()
                    }
                }
                return Promise.reject(err)
            })
            interceptorsAttached = true
        },
        // 使用jsencrypt加密密码
        encryptPassword(password) {
            if (!this.pubkeyPem) {
                return null
            }
            try {
                const encrypt = new JSEncrypt()
                encrypt.setPublicKey(this.pubkeyPem)
                return encrypt.encrypt(password)
            } catch (e) {
                console.error('Failed to encrypt password:', e)
                return null
            }
        },
        async login(email, password) {
            this.loading = true
            this.error = null
            try {
                this.ensureInterceptors()
                // 强制刷新公钥，确保使用最新的密钥
                await this.ensureCrypto(true)
                
                let payload = { email, password } // 默认使用明文
                
                // 尝试使用jsencrypt加密密码
                const enc_password = this.encryptPassword(password)
                if (enc_password) {
                    payload = { email, enc_password }
                }
                
                const r = await api.post(`/auth/login`, payload)
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
        async register(email, password, companyName = null) {
            this.loading = true
            this.error = null
            try {
                this.ensureInterceptors()
                // 强制刷新公钥，确保使用最新的密钥
                await this.ensureCrypto(true)
                
                let payload = { email, password, company_name: companyName } // 默认使用明文
                
                // 尝试使用jsencrypt加密密码
                const enc_password = this.encryptPassword(password)
                if (enc_password) {
                    payload = { email, enc_password, company_name: companyName }
                }
                
                await api.post(`/auth/register`, payload)
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
