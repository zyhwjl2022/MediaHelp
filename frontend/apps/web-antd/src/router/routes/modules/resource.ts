import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'ic:baseline-view-in-ar',
      // keepAlive: true,
      order: 1000,
      title: '资源搜索',
    },
    name: 'Resource',
    path: '/resource',
    component: () => import('#/views/resource/index.vue'),
  },
];

export default routes;
