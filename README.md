需要自行构建： 
librenderdoc.so
qrenderdoc.so
renderdoc.so

git clone https://github.com/baldurk/renderdoc.git
cd renderdoc
mkdir build_release
cmake -DCMAKE_BUILD_TYPE=Release -Bbuild_release -H.
make -C build_release -j7

