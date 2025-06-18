import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'ic:baseline-view-in-ar',
      keepAlive: true,
      order: 2000,
      title: '定时任务',
    },
    name: 'CornTask',
    path: '/cornTask',
    children: [
      {
        meta: {
          title: '定时任务管理',
        },
        name: 'CornTaskList',
        path: '/cornTask/list',
        component: () => import('#/views/cornTask/list.vue'),
      },
      {
        meta: {
          title: '定时任务日志',
        },
        name: 'CornTaskLog',
        path: '/cornTask/log',
        component: () => import('#/views/cornTask/log.vue'),
      },
    ],
  },
];

export default routes;
