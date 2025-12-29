import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
// import TaskView from '../views/TaskView.vue'
import SftView from '../views/tasks/SftView.vue'
import RlView from '../views/tasks/RlView.vue'
import InferView from '../views/tasks/InferView.vue'
import EvalView from '../views/tasks/EvalView.vue'
import ExportView from '../views/tasks/ExportView.vue'
import SampleView from '../views/tasks/SampleView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: Dashboard,
      meta: { requiresAuth: true }
    },
    // Individual Module Routes
    {
      path: '/training/sft',
      name: 'sft',
      component: SftView,
      meta: { requiresAuth: true }
    },
    {
      path: '/training/rl',
      name: 'rl',
      component: RlView,
      meta: { requiresAuth: true }
    },
    {
      path: '/training/rlhf',
      redirect: '/training/rl'
    },
    {
      path: '/training/dpo',
      redirect: '/training/rl'
    },
    {
      path: '/training/grpo',
      redirect: '/training/rl'
    },
    {
      path: '/training/infer',
      name: 'infer',
      component: InferView,
      meta: { requiresAuth: true }
    },
    {
      path: '/training/eval',
      name: 'eval',
      component: EvalView,
      meta: { requiresAuth: true }
    },
    {
      path: '/training/export',
      name: 'export',
      component: ExportView,
      meta: { requiresAuth: true }
    },
    {
      path: '/training/sample',
      name: 'sample',
      component: SampleView,
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
