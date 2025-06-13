<script setup lang="ts">
import type { PropType } from 'vue';

import { computed, onMounted, onUnmounted, ref, watch } from 'vue';

import { Button, message, Modal } from 'ant-design-vue';

import FolderSelect from '../FolderSelect/index.vue';
import {
  getCloud189FileListApi,
  getCloud189ShareFileListApi,
  getQuarkFileListApi,
  getQuarkShareFileListApi,
  saveCloud189FileApi,
  saveQuarkFileApi,
} from './api';

const props = defineProps({
  item: {
    type: Object as PropType<any>,
    default: () => ({}),
  },
});
const shareUrl = computed(() => {
  return props.item?.cloudLinks?.[0] || '';
});
const fileList = ref<any[]>([]);
const selectedFile = ref<any[]>([]);
const stoken = ref<string>('');
const paths = ref<any[]>([]);
const fileList2 = ref<any[]>([]);
const paths2 = ref<any[]>([]);
const open = defineModel<boolean>('open', {
  default: false,
  type: Boolean,
});
const loading = defineModel<boolean>('loading', {
  default: false,
  type: Boolean,
});
const saveOperation = ['分享文件', '保存到'];
const currentStep = ref<number>(0);
const okText = computed(() => {
  return currentStep.value === 0 ? '保存到' : '保存';
});
const modalTitle = computed(() => {
  return saveOperation[currentStep.value];
});

const width = ref('800px');

const updateWidth = () => {
  const w = window.innerWidth;
  if (w < 640) {
    width.value = '90vw';
  } else if (w < 768) {
    width.value = '800px';
  } else if (w < 1024) {
    width.value = '1000px';
  } else if (w < 1280) {
    width.value = '1000px';
  } else {
    width.value = '1000px';
  }
};

onMounted(() => {
  updateWidth();
  window.addEventListener('resize', updateWidth);
});

onUnmounted(() => {
  window.removeEventListener('resize', updateWidth);
});

let lastShareUrl: any;
const formatQuarkShareUrl = (dir: any = {}) => {
  const url = lastShareUrl ?? shareUrl.value;
  if (Object.keys(dir).length === 0 || dir.fid === 0) {
    lastShareUrl = url.match(/.*s\/[a-z0-9]+(\?pwd=[^#]+)?/)?.[0] || '';
    return lastShareUrl;
  } else if (url.includes(dir.fid)) {
    lastShareUrl = url.match(new RegExp(`.*/${dir.fid}[^/]*`))?.[0] || '';
    return lastShareUrl;
  } else if (url.includes('#/list/share')) {
    lastShareUrl = `${url}/${dir.fid}-${dir.name?.replace(/-/g, '*101')}`;
    return lastShareUrl;
  } else {
    lastShareUrl = `${url}#/list/share/${dir.fid}-${dir.name?.replace(/-/g, '*101')}`;
    return lastShareUrl;
  }
};
let filePaths: any[] = [];
const selfSavePaths = (dir: any, filePaths: any[]) => {
  if (dir.fid) {
    const index = filePaths.findIndex((item) => item.fid === dir.fid);
    if (index === -1) {
      filePaths.push(dir);
    } else {
      filePaths = filePaths.slice(0, index + 1);
    }
  } else {
    filePaths = [];
  }
};
const getShareFileList = async (dir: any = {}) => {
  if (props.item?.cloudType === 'quark') {
    loading.value = true;
    const res = await getQuarkShareFileListApi({
      share_url: formatQuarkShareUrl(dir),
    }).finally(() => {
      loading.value = false;
    });
    fileList.value = res.list ?? [];
    paths.value = res.paths ?? [];
    stoken.value = res?.share_info?.token ?? '';
  } else if (props.item?.cloudType === 'tianyiyun') {
    loading.value = true;
    const res = await getCloud189ShareFileListApi({
      share_url: shareUrl.value,
      file_id: dir.fid,
    }).finally(() => {
      loading.value = false;
    });
    const { fileListAO } = res;
    fileList.value = [
      ...(fileListAO?.folderList ?? []).map((item: any) => ({
        ...item,
        file_name: item.name,
        fid: item.id,
        dir: true,
      })),
      ...(fileListAO?.fileList ?? []).map((item: any) => ({
        ...item,
        file_name: item.name,
        fid: item.id,
        file: true,
      })),
    ];
    if (dir.fid) {
      // 如果当前目录有fid，则将当前目录添加到filepaths中
      const index = filePaths.findIndex((item) => item.fid === dir.fid);
      if (index === -1) {
        filePaths.push(dir);
      } else {
        filePaths = filePaths.slice(0, index + 1);
      }
    } else {
      filePaths = [];
    }
    selfSavePaths(dir, filePaths);
    paths.value = [...filePaths];
  }
};
const filepaths2: any[] = [];
const getFileList = async (dir: any = {}) => {
  if (props.item?.cloudType === 'quark') {
    loading.value = true;
    const res = await getQuarkFileListApi({ dir_id: dir.fid }).finally(() => {
      loading.value = false;
    });
    fileList2.value = res.list ?? [];
    selfSavePaths(dir, filepaths2);
    paths2.value = [...filepaths2];
  } else {
    loading.value = true;
    const res = await getCloud189FileListApi({
      folder_id: dir.fid === undefined ? '-11' : String(dir.fid),
    }).finally(() => {
      loading.value = false;
    });
    const { fileListAO } = res;
    fileList2.value = [
      ...(fileListAO?.folderList ?? []).map((item: any) => ({
        ...item,
        file_name: item.name,
        fid: item.id,
        dir: true,
      })),
      ...(fileListAO?.fileList ?? []).map((item: any) => ({
        ...item,
        file_name: item.name,
        fid: item.id,
        file: true,
      })),
    ];
    if (dir.fid) {
      // 如果当前目录有fid，则将当前目录添加到filepaths中
      const index = filePaths.findIndex((item) => item.fid === dir.fid);
      if (index === -1) {
        filePaths.push(dir);
      } else {
        filePaths = filePaths.slice(0, index + 1);
      }
    } else {
      filePaths = [];
    }
    selfSavePaths(dir, filePaths);
    paths2.value = [...filePaths];
  }
};

const saveShareFile = async () => {
  if (props.item?.cloudType === 'quark') {
    const file_ids = selectedFile.value.map((item) => item.fid);
    const file_tokens = selectedFile.value.map((item) => item.share_fid_token);
    const target_dir = paths2.value[paths2.value.length - 1]?.fid ?? '0';
    const pdir_fid = paths.value[paths.value.length - 1]?.fid ?? '0';
    return await saveQuarkFileApi({
      share_url: shareUrl.value,
      file_ids,
      file_tokens,
      target_dir,
      pdir_fid,
      stoken: stoken.value,
    });
  } else if (props.item?.cloudType === 'tianyiyun') {
    const target_folder_id =
      paths2.value[paths2.value.length - 1]?.fid ?? '-11';
    const file_ids = selectedFile.value.map((item) => ({
      fileId: item.fid,
      fileName: item.file_name,
      isFolder: item.dir,
    }));
    return await saveCloud189FileApi({
      share_url: shareUrl.value,
      target_folder_id,
      file_ids,
    });
  }
};

watch(open, (value) => {
  if (value) {
    lastShareUrl = undefined;
    fileList.value = [];
    fileList2.value = [];
    paths.value = [];
    paths2.value = [];
    selectedFile.value = [];
    currentStep.value = 0;
    getShareFileList();
  }
});

const navigateTo = (dir: any) => {
  if (currentStep.value === 0) {
    getShareFileList(dir);
  } else {
    getFileList(dir);
  }
};

const onOk = async () => {
  if (currentStep.value === 0) {
    // 下一步
    currentStep.value = 1;
    if (fileList2.value.length === 0) {
      getFileList();
    }
  } else {
    // 保存
    await saveShareFile();
    open.value = false;
    message.success('保存成功');
  }
};

const onBack = () => {
  currentStep.value = 0;
};
</script>

<template>
  <Modal
    v-model:open="open"
    :title="modalTitle"
    :width="width"
    destroy-on-close
  >
    <div v-loading="loading" v-show="currentStep === 0">
      <FolderSelect
        v-model:selected-file="selectedFile"
        :file-list="fileList"
        :paths="paths"
        @navigate-to="navigateTo"
      />
    </div>
    <div v-loading="loading" v-show="currentStep === 1">
      <FolderSelect
        :if-use-checkbox="false"
        :file-list="fileList2"
        :paths="paths2"
        @navigate-to="navigateTo"
      />
    </div>
    <template #footer>
      <Button @click="onBack" v-show="currentStep === 1"> 返回 </Button>
      <Button type="primary" @click="onOk">{{ okText }}</Button>
    </template>
  </Modal>
</template>
