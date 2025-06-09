import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'ic:baseline-view-in-ar',
      keepAlive: true,
      order: 1000,
      title: '系统配置',
    },
    name: 'SysConfig',
    path: '/sys-config',
    component: () => import('#/views/sysConfig/index.vue'),
  },
];

export default routes;
