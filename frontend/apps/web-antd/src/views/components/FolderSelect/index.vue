<script setup lang="ts">
import type { PropType } from 'vue';

import { h, onMounted, ref, watch } from 'vue';

import {
  MdiCreateDir,
  MdiDelete,
  MdiFile,
  MdiFolder,
  MdiHome,
  MdiRename,
  MdiSave,
} from '@vben/icons';

import {
  Breadcrumb,
  BreadcrumbItem,
  Button,
  Checkbox,
  CheckboxGroup,
  Input,
  message,
  Modal,
} from 'ant-design-vue';

const props = defineProps({
  fileList: {
    type: Array as PropType<any[]>,
    default: () => [],
  },
  paths: {
    type: Array as PropType<any[]>,
    default: () => [],
  },
  ifUseCheckbox: {
    type: Boolean,
    default: true,
  },
  ifUseFileManager: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['navigateTo', 'rename', 'delete', 'createDir']);

const isEditing = ref<any>({});

const selectedFile = defineModel<any[]>('selectedFile', {
  default: () => [],
});
const selectedFileFids = ref<any[]>([]);
const selectAll = ref<boolean>(false);

watch(selectAll, (value) => {
  selectedFile.value = value ? props.fileList : [];
  selectedFileFids.value = value ? props.fileList.map((item) => item.fid) : [];
});

watch(selectedFileFids, (value) => {
  selectedFile.value = props.fileList.filter((item) =>
    value.includes(item.fid),
  );
});
watch(
  () => props.fileList,
  (value) => {
    // 初始化编辑状态
    value.forEach((item) => {
      isEditing.value[item.fid] = false;
    });
  },
);

onMounted(() => {
  props.fileList.forEach((item) => {
    isEditing.value[item.fid] = false;
  });
});

const navigateTo = (file: any) => {
  if (file.dir && !isEditing.value[file.fid]) {
    emit('navigateTo', { fid: file.fid, name: file.file_name });
  }
};
const fileNameEditing = ref<any>('');
const onCreateDir = () => {
  fileNameEditing.value = '';
  const modal = Modal.confirm({
    title: '新建文件夹',
    type: 'info',
    content: h(Input, {
      onChange: (e: any) => {
        fileNameEditing.value = e.target.value;
      },
      placeholder: '请输入文件夹名称',
      style: {
        width: '100%',
        height: '35px',
      },
      onKeyup: (e: any) => {
        if (e.key === 'Enter') {
          modal.destroy();
          emit('createDir', fileNameEditing.value);
        }
      },
    }),
    onOk: () => {
      emit('createDir', fileNameEditing.value);
    },
  });
};

const onRename = (file: any) => {
  const isEditingFileArr = Object.keys(isEditing.value).map(
    (item) => isEditing.value[item],
  );
  if (isEditingFileArr.includes(true)) {
    message.error('请先保存正在编辑的文件');
    return;
  }
  isEditing.value[file.fid] = {
    isEditing: true,
  };
  fileNameEditing.value = file.file_name;
};

const onDelete = (file: any) => {
  isEditing.value[file.fid] = false;
  emit('delete', file);
};

const onSave = (file: any) => {
  isEditing.value[file.fid] = false;
  if (file.file_name === fileNameEditing.value) {
    return;
  }
  emit('rename', { ...file, file_name: fileNameEditing.value });
};
</script>
<template>
  <div>
    <div>
      <Breadcrumb>
        <BreadcrumbItem class="cursor-pointer" @click="emit('navigateTo', {})">
          <MdiHome class="inline-block text-xl" />
        </BreadcrumbItem>
        <BreadcrumbItem
          v-for="path in paths"
          :key="path.fid"
          class="cursor-pointer"
          @click="emit('navigateTo', { fid: path.fid, name: path.name })"
        >
          {{ path.name }}
        </BreadcrumbItem>
      </Breadcrumb>
    </div>
    <div
      class="mt-4 max-h-[60vh] overflow-y-auto overflow-x-hidden border-b border-t"
    >
      <div class="ml-5 mt-3 flex w-full items-center justify-between">
        <Checkbox v-model:checked="selectAll" v-if="ifUseCheckbox">
          全选
        </Checkbox>
        <div class="flex items-center gap-2 pr-5">
          <Button type="primary" @click="onCreateDir" v-if="ifUseFileManager">
            <MdiCreateDir class="text-xl" />新建文件夹
          </Button>
        </div>
      </div>
      <div class="p-3">
        <CheckboxGroup v-model:value="selectedFileFids" class="w-full">
          <div
            class="flex min-h-[50px] w-full cursor-pointer items-center rounded-lg border"
            v-for="file in fileList"
            :key="file.fid"
          >
            <Checkbox :value="file.fid" class="ml-2" v-if="ifUseCheckbox" />
            <MdiFolder
              class="ml-2 mr-2 text-2xl"
              v-if="file.dir"
              @click="navigateTo(file)"
            />
            <MdiFile
              class="ml-2 mr-2 text-2xl"
              v-if="file.file"
              @click="navigateTo(file)"
            />
            <div
              class="group relative h-full w-[calc(100%-25px)] leading-[50px]"
              @click="navigateTo(file)"
            >
              <div class="w-full truncate" v-show="!isEditing?.[file.fid]">
                {{ file.file_name }}
              </div>
              <Input
                v-model:value="fileNameEditing"
                v-show="isEditing?.[file.fid]"
                @keyup.enter="onSave(file)"
              />
              <div
                class="absolute right-0 top-0 hidden group-hover:block"
                v-if="ifUseFileManager"
              >
                <Button
                  type="link"
                  v-show="!isEditing?.[file.fid]"
                  @click.stop="onRename(file)"
                  class="pl-2 pr-2"
                >
                  <MdiRename class="text-xl" />重命名
                </Button>
                <Button
                  type="link"
                  v-show="isEditing?.[file.fid]"
                  @click.stop="onSave(file)"
                  class="pl-2 pr-2"
                >
                  <MdiSave class="text-xl" />保存
                </Button>
                <Button
                  type="link"
                  @click.stop="onDelete(file)"
                  class="pl-2 pr-2"
                  danger
                >
                  <MdiDelete class="text-xl" />删除
                </Button>
              </div>
            </div>
          </div>
        </CheckboxGroup>
      </div>
    </div>
  </div>
</template>
