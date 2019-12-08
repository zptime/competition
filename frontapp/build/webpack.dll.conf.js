/**
 * 打包第三方依赖的库文件
 */
const path = require('path');
const webpack = require('webpack');
const AssetsPlugin = require('assets-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const config = require('../config');
const env = config.build.env;

module.exports = {
  entry: {
    libs: [
      'vue/dist/vue.common.js',
      'vue-router',
      'vuex',
      'babel-polyfill',
      'axios',
      'element-ui',
      'echarts',
    ]
  },
  output: {
    path: path.resolve(__dirname, '../libs'),//打包后文件输出的位置
    filename: '[name].[chunkhash:7].js',//打包文件的名字
    library: '[name]_library',//可选 暴露出的全局变量名，主要是给DllPlugin中的name使用，故这里需要和webpack.DllPlugin中的`name: '[name]_library',`保持一致。
  },
  plugins: [
    new webpack.DefinePlugin({
      'process.env': env,
    }),
    new webpack.DllPlugin({
      path: path.resolve(__dirname, '../libs/[name]-mainfest.json'),//生成上文说到清单文件
      name: '[name]_library',
      context: __dirname, // 执行的上下文环境，对之后DllReferencePlugin有用
    }),
    new ExtractTextPlugin('[name].[contenthash:7].css'),
    new webpack.optimize.UglifyJsPlugin({
      compress: {
        warnings: false,//删除无用代码时不输出警告
        drop_console:true,//删除所有console语句，可以兼容IE
        drop_debugger:true
      },
      output:{
        comments: false,// 去掉注释内容
        beautify: false, //最紧凑的输出，不保留空格和制表符
      },
      sourceMap: true
    }),
    new AssetsPlugin({
      filename: 'bundle-config.json',
      path: './libs',
    }),
    new CleanWebpackPlugin(['libs'], {
      root: path.join(__dirname, '../'), // 绝对路径
      verbose: true,
      dry: false,
    }),
  ],
  module: {
    rules: [
      {
        test: /\.js$/,
        loader: 'babel-loader',
      },
    ],
  },
};
