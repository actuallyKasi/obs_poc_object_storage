const path = require('path');
module.exports = {entry:'./src/module.tsx',output:{path:path.resolve(__dirname,'dist'),filename:'module.js',library:{type:'amd'}},externals:[/^@grafana\//,'react','react-dom','rxjs','react/jsx-runtime'],module:{rules:[{test:/\.tsx?$/,loader:'ts-loader',exclude:/node_modules/}]},resolve:{extensions:['.ts','.tsx','.js']}};
