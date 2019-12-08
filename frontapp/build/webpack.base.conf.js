/**
 * webpack开发环境和生成环境通用的配置
 */
'use strict'
const path = require('path')
const webpack = require('webpack')
const utils = require('./utils')
const config = require('../config')
const vueLoaderConfig = require('./vue-loader.conf')
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
const HappyPack = require('happypack');
const os = require('os');
const happyThreadPool = HappyPack.ThreadPool({ size: os.cpus().length });

//获取对应文件路径的函数
//因为该文件是在项目的二级文件build下，所以要加上../这样才能找到像src这样的目录
function resolve (dir) {
  //join方法用于将多个字符串结合成一个路径字符串
  //path在node中会经常用到可以仔细了解一下path的各种方法
  //__dirname：获取当前文件所在目录的完整绝对路径
  return path.join(__dirname, '..', dir)
}

module.exports = {
  context: path.resolve(__dirname, '../'),
  entry: {
    app: ["babel-polyfill", "./src/main.js"],
  },
  output: {
    path: config.build.assetsRoot,
    filename: '[name].js',
    libraryTarget: 'umd',
    publicPath: process.env.NODE_ENV === 'production'
      ? config.build.assetsPublicPath
      : config.dev.assetsPublicPath
  },
  externals: {
    'jquery': 'window.jQuery',
    'vue': 'Vue',
    'element-ui': 'ELEMENT',
    'vue-router': 'VueRouter',
    'axios': 'axios',
  },
  resolve: {
    //自动解析确定的扩展,在引入模块时不带扩展名
    //例如：import somejs from "@/some"
    extensions: ['.js', '.vue', '.json'],
    alias: {
      // 后面的$符号指精确匹配
      // 也就是说只能使用 import vuejs from "vue" 这样的方式导入vue.esm.js文件
      'vue$': 'vue/dist/vue.esm.js',
      // resolve('src') 其实在这里就是项目根目录中的src目录
      // 例如引用src目录下的some.js方法:import somejs from "@/some.js"
      // 用@来代替../src
      '@': resolve('src'),
      'images': path.resolve(__dirname, '../src/images'),
      'components': path.resolve(__dirname, '../src/components')
    }
  },
  module: {
    rules: [
      {
        test: /\.vue$/,
        loader: 'vue-loader',
        options: vueLoaderConfig,
        // exclude: /node_modules\/(?!(autotrack|dom-utils))|vendor\.dll\.js/
      },
      {
        test: /\.js$/,
        loader: 'happypack/loader?id=happy-babel-js',
        include: [
          resolve('src'),
          resolve('test'),
          resolve('node_modules/webpack-dev-server/client'),
          resolve('node_modules/element-ui/src'),
          resolve('node_modules/element-ui/packages'),
        ],
        // 排除 node_modules 目录下的文件，node_modules 目录下的文件都是采用的 ES5 语法，没必要再通过 Babel 去转换
        // exclude: /node_modules/
        // exclude: /node_modules\/element-ui\/src\/(utils\/popper\.js|utils\/date.\js)/
      },
      {
        test: /\.(png|jpe?g|gif|svg)(\?.*)?$/,
        loader: ['url-loader?limit=10000&name='+utils.assetsPath('img/[name].[hash:7].[ext]'),
          'image-webpack-loader'
        ]
      },
      {
        test: /\.(mp4|webm|ogg|mp3|wav|flac|aac)(\?.*)?$/,
        loader: 'url-loader',
        options: {
          limit: 10000,
          name: utils.assetsPath('media/[name].[hash:7].[ext]')
        }
      },
      {
        test: /\.(woff2?|eot|ttf|otf)(\?.*)?$/,
        loader: 'url-loader',
        options: {
          limit: 10000,
          name: utils.assetsPath('fonts/[name].[hash:7].[ext]')
        }
      },
      {
        test: require.resolve('jquery'),
        use: [{
          loader: 'expose-loader',
          options: 'jQuery'
        },{
          loader: 'expose-loader',
          options: '$'
        }]
      }
    ]
  },
  plugins: [
    // new BundleAnalyzerPlugin(),
    new webpack.ProvidePlugin({
      $: 'jquery',
      jQuery: 'jquery',
      'window.jQuery': 'jquery',
      'window.$': 'jquery'
    }),
    new HappyPack({
      id: 'happy-babel-js',
      loaders: ['babel-loader?cacheDirectory=true'],
      threadPool: happyThreadPool
    })
  ],
  node: {
    // prevent webpack from injecting useless setImmediate polyfill because Vue
    // source contains it (although only uses it if it's native).
    setImmediate: false,
    // prevent webpack from injecting mocks to Node native modules
    // that does not make sense for the client
    dgram: 'empty',
    fs: 'empty',
    net: 'empty',
    tls: 'empty',
    child_process: 'empty'
  }
}
