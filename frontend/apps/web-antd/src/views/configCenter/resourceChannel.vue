<script lang="ts" setup>
import type { VxeGridProps } from '#/adapter/vxe-table';

import { Button, message } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';

import {
  getResourceChannelConfigApi,
  updateResourceChannelConfigApi,
} from './api';

interface RowType {
  category: string;
  color: string;
  id: string;
  price: string;
  productName: string;
  releaseDate: string;
}

const gridOptions: VxeGridProps<RowType> = {
  columns: [
    { title: '序号', type: 'seq', width: 50 },
    { editRender: { name: 'input' }, field: 'id', title: '频道ID' },
    { editRender: { name: 'input' }, field: 'name', title: '频道名称' },
    // { slots: { default: 'action' }, title: '操作' },
  ],
  editConfig: {
    trigger: 'click',
    mode: 'row',
  },
  pagerConfig: {
    enabled: false,
  },
  proxyConfig: {
    enabled: true,
    ajax: {
      query: async () => {
        const { telegram } = await getResourceChannelConfigApi({});
        return {
          items: telegram?.channels,
        };
      },
    },
  },
  showOverflow: true,
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

const addRowEvent = () => {
  gridApi.grid.insert({
    category: '',
    color: '',
  });
};

const saveConfigEvent = async () => {
  const data = gridApi.grid.getTableData();
  await updateResourceChannelConfigApi({
    channels: data.tableData,
  });
  message.success('保存成功');
};
</script>

<template>
  <div class="vp-raw w-full p-[20px]">
    <Grid>
      <template #toolbar-tools>
        <Button type="primary" @click="addRowEvent" class="mr-[10px]">
          新增
        </Button>
        <Button type="primary" @click="saveConfigEvent">保存配置</Button>
      </template>
    </Grid>
  </div>
</template>
