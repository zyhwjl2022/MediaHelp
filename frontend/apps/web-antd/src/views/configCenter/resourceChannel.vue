<script lang="ts" setup>
import type { VxeGridProps } from '#/adapter/vxe-table';

import { onActivated, onMounted, ref } from 'vue';

import {
  Affix,
  Button,
  Divider,
  Form,
  FormItem,
  Input,
  message,
  Switch,
} from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';

import {
  getProxyConfigApi,
  getResourceChannelConfigApi,
  updateProxyConfigApi,
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
const proxyConfig = ref<any>({});
const gridOptions: VxeGridProps<RowType> = {
  columns: [
    { title: '序号', type: 'seq', width: 50 },
    { editRender: { name: 'input' }, field: 'id', title: '频道ID', width: 100 },
    {
      editRender: { name: 'input' },
      field: 'name',
      title: '频道名称',
      width: 100,
    },
    {
      slots: { default: 'action' },
      title: '操作',
      minWidth: 200,
      fixed: 'right',
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
  await Promise.all([
    updateResourceChannelConfigApi({
      channels: data.tableData,
    }),
    updateProxyConfigApi({
      use_proxy: proxyConfig.value.use_proxy,
      proxy_host: proxyConfig.value.proxy_host,
      proxy_port: proxyConfig.value.proxy_port,
    }),
  ]);
  message.success('保存成功');
};

onMounted(() => {
  getProxyConfigApi({}).then((res) => {
    proxyConfig.value = res;
  });
});
onActivated(() => {
  getProxyConfigApi({}).then((res) => {
    proxyConfig.value = res;
  });
});

const deleteRowEvent = (row: RowType) => {
  gridApi.grid.remove(row);
};

const upRowEvent = (row: RowType) => {
  const { tableData } = gridApi.grid.getTableData();
  const index = tableData.findIndex((item: RowType) => item.id === row.id);
  if (index > 0) {
    const temp = tableData[index - 1];
    tableData[index - 1] = row;
    tableData[index] = temp;
    gridApi.grid.reloadData(tableData);
  }
};

const downRowEvent = (row: RowType) => {
  const { tableData } = gridApi.grid.getTableData();
  const index = tableData.findIndex((item: RowType) => item.id === row.id);
  if (index < tableData.length - 1) {
    const temp = tableData[index + 1];
    tableData[index + 1] = row;
    tableData[index] = temp;
    gridApi.grid.reloadData(tableData);
  }
};
</script>

<template>
  <div class="vp-raw w-full p-[20px]">
    <Divider>代理设置</Divider>
    <Form layout="inline">
      <FormItem label="是否启用代理" name="use_proxy" class="w-full pb-[10px]">
        <Switch v-model:checked="proxyConfig.use_proxy" />
      </FormItem>
      <FormItem label="代理地址" name="proxy_host" class="w-[calc(50%-30px)]">
        <Input v-model:value="proxyConfig.proxy_host" />
      </FormItem>
      <FormItem label="代理端口" name="proxy_port" class="w-[calc(50%-30px)]">
        <Input v-model:value="proxyConfig.proxy_port" />
      </FormItem>
    </Form>
    <Grid class="mb-[20px] mt-[20px]">
      <template #toolbar-tools>
        <Button type="primary" @click="addRowEvent" class="mr-[10px]">
          新增
        </Button>
      </template>
      <template #action="{ row }">
        <Button type="link" @click="upRowEvent(row)">上移</Button>
        <Button type="link" @click="downRowEvent(row)">下移</Button>
        <Button type="link" @click="deleteRowEvent(row)" danger>删除</Button>
      </template>
    </Grid>
    <Affix :offset-bottom="50">
      <div class="mr-[20px] flex justify-end">
        <Button type="primary" @click="saveConfigEvent">保存配置</Button>
      </div>
    </Affix>
  </div>
</template>
