<script setup lang="ts">
import type { VxeGridProps } from '#/adapter/vxe-table';

import { onActivated, onMounted, ref } from 'vue';

import { cloneDeep } from '@vben/utils';

import { Button, message, Switch } from 'ant-design-vue';
import dayjs from 'dayjs';

import { useVbenVxeGrid } from '#/adapter/vxe-table';

import {
  deleteCornTaskApi,
  disableCornTaskApi,
  enableCornTaskApi,
  getCornTaskListApi,
} from './api';
import TaskEditor from './components/TaskEditor.vue';

const open = ref(false);
const currentTask = ref<any>({});
const gridOptions: VxeGridProps = {
  minHeight: 500,
  columns: [
    { title: '序号', type: 'seq', width: 50 },
    { field: 'name', title: '任务名称' },
    {
      field: 'next_run',
      title: '下次运行时间',
      formatter: ({ cellValue }): string => {
        if (cellValue) {
          return dayjs(cellValue).format('YYYY-MM-DD HH:mm:ss');
        }
        return '';
      },
    },
    {
      field: 'enabled',
      title: '状态',
      slots: {
        default: 'enabled',
      },
    },
    {
      field: 'task',
      title: '任务类型',
      formatter: ({ cellValue }): string => {
        if (cellValue === 'quark_auto_save') {
          return '夸克自动转存';
        }
        if (cellValue === 'cloud189_auto_save') {
          return '天翼自动转存';
        }
        return '';
      },
    },
    {
      field: 'action',
      title: '操作',
      fixed: 'right',
      width: 180,
      slots: {
        default: 'action',
      },
    },
  ],
  editConfig: {
    trigger: 'click',
    mode: 'row',
  },
  pagerConfig: {
    enabled: false,
  },
  proxyConfig: {
    enabled: false,
  },
  showOverflow: true,
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

const reload = () => {
  getCornTaskListApi().then((res: any) => {
    gridApi.grid.loadData(res || []);
  });
};

onMounted(() => {
  reload();
});

onActivated(() => {
  reload();
});

const addRowEvent = () => {
  currentTask.value = {};
  open.value = true;
};

const editRowEvent = (_row: any) => {
  currentTask.value = cloneDeep(_row);
  open.value = true;
};

const deleteRowEvent = (_row: any) => {
  deleteCornTaskApi(_row.name).then(() => {
    message.success('删除成功');
    reload();
  });
};

const handleSwitchEvent = (row: any) => {
  if (row.enabled) {
    disableCornTaskApi(row.name).then(() => {
      message.success('禁用成功');
      reload();
    });
  } else {
    enableCornTaskApi(row.name).then(() => {
      message.success('启用成功');
      reload();
    });
  }
};
</script>
<template>
  <div class="h-full">
    <Grid class="mt-0">
      <template #toolbar-tools>
        <Button type="primary" @click="addRowEvent" class="mb-2 mr-[10px] mt-2">
          创建定时任务
        </Button>
      </template>
      <template #enabled="{ row }">
        <Switch :checked="row.enabled" @click="handleSwitchEvent(row)" />
        <span :class="row.enabled ? 'text-green-500' : 'text-red-500'">{{
          row.enabled ? ' 启用' : ' 禁用'
        }}</span>
      </template>
      <template #action="{ row }">
        <Button type="link" @click="editRowEvent(row)">编辑</Button>
        <Button type="link" @click="deleteRowEvent(row)" danger>删除</Button>
      </template>
    </Grid>
    <TaskEditor v-model:open="open" :task="currentTask" @success="reload" />
  </div>
</template>
