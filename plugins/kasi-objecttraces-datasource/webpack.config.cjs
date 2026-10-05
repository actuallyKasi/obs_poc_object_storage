// Use classic JSX (tsconfig) with Grafana's shared React; its AMD loader does not expose react/jsx-runtime.
const path = require('path');
module.exports = {entry:'./src/module.tsx',output:{path:path.resolve(__dirname,'dist'),filename:'module.js',library:{type:'amd'}},externals:[/^@grafana\//,'react','react-dom','rxjs'],module:{rules:[{test:/\.tsx?$/,loader:'ts-loader',exclude:/node_modules/}]},resolve:{extensions:['.ts','.tsx','.js']}};
