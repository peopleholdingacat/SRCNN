
import settings
import tensorflow as tf
import os
import numpy as np
from tensorflow.keras.layers import (Dense, Conv2D, LayerNormalization,
                                     Layer, Dropout, Input, GlobalAveragePooling1D, Embedding,Reshape)
from tensorflow.keras import Sequential, Model
from data import makedataset
from  datetime import datetime
from loss import loss_cos
from model import SRCNN as srcnn
from eval import PSNR
if settings.gpu:
    gpus = tf.config.list_physical_devices("GPU")
    print(gpus)
    if gpus:
        gpu0 = gpus[0] #如果有多个GPU，仅使用第0个GPU
        tf.config.experimental.set_memory_growth(gpu0, True) #设置GPU显存用量按需使用
        # 或者也可以设置GPU显存为固定使用量(例如：4G)
        #tf.config.experimental.set_virtual_device_configuration(gpu0,
        #    [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=4096)])
        tf.config.set_visible_devices([gpu0],"GPU")
else:
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
logdir = "logs/" + datetime.now().strftime("%Y%m%d-%H%M%S")
if settings.loss=="CategoricalCrossentropy":
    loss=tf.keras.losses.CategoricalCrossentropy()
elif settings.loss=="MSE":
     loss=tf.keras.losses.MeanAbsoluteError()
elif settings.loss=="":
    loss=loss_cos
else:
    raise EnvironmentError("loss函数意外丢失")
optimizer=tf.keras.optimizers.Adam(learning_rate=settings.lr)
train_accuracy =tf.keras.metrics.SparseCategoricalAccuracy(name='train_accuracy')
class   MODELErro(Exception):
    def __init__(self,ARG):
        self.fp=None
        with open("paint.txt","a+") as fp:
            self.fp=fp
        self.str_ARG1 =ARG

    def __str__(self):
        return "model error:没有{}这个模型".format(self.str_ARG1)
class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs):
    print(epoch)
    #logs如下
    """
    {'loss': 0.35939720273017883, 'accuracy': 0.5134039521217346, 'val_loss': 0.2836693525314331, 'val_accuracy': 0.476856529712677}
    """
    """
    写入loss等基本信息
    epch,loss,accuracy,val_loss,val_accuracy
    """
    self.fp.write(str(epoch)+","+str(logs["loss"])+","+str(logs["accuracy"])+","+str(logs["val_loss"])+","+str(logs["val_accuracy"])+"\n")



def train():
    train_dataset,val_dataset=makedataset(settings.datapath)
    print(train_dataset)
    inputs = Input(shape=(settings.x, settings.y, 3), batch_size=settings.batch)
    if settings.model=="SRCNN":
        models = srcnn()
    else:
        raise MODELErro(settings.model)
    out = models(inputs)
    model = Model(inputs=inputs, outputs=out, name='transformers-tf2')
    model.summary()

    # #Input(shape=(3000,2), batch_size=32)
    # model.build(input_shape=(3000,2))
    # print(model)
#    model.load_weights(os.path.join(setting.save_path, 'transformers_{0}.h5'.format(str(setting.initial_epoch))))
    callbacks = [
        # 模型保存
        tf.keras.callbacks.ModelCheckpoint(
            os.path.join(settings.save_path, str(settings.model)+"{epoch}.h5"),
            monitor='val_loss',
            save_weights_only=True,
            verbose=1
        ),
        # tf.keras.callbacks.EarlyStopping(monitor='val_loss',
        #                                  patience=20,
        #                                  restore_best_weights=True),
        tf.keras.callbacks.TensorBoard(
            log_dir='logs', histogram_freq=0, write_graph=True, write_images=False,
            update_freq='epoch', profile_batch=2, embeddings_freq=0,
            embeddings_metadata=None,
        ),
        myCallback()

       # tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=0.00000001)
    ]
    # 查看模型结构
    model.summary()
    model.compile(
        optimizer=optimizer,
        loss=loss,
        metrics=['accuracy']
    )
    model.fit(
        train_dataset,
        epochs=settings.epoch,
        # steps_per_epoch=train_dataset_size // settings.batch,
        initial_epoch=settings.initial_epoch,
        validation_data=val_dataset,
        # validation_steps=val_dataset_size // settings.batch,
        callbacks=callbacks,

    )
