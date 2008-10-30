#include "util.cu"
#include "math.cu"
#include "seed.cu"
#include "color.cu"

texture<float4, 2, cudaReadModeElementType> input_texture;

extern "C" {

  __device__ float4 get_seed(float2 z)
  {
    return fade_frame(z);
  }

  __device__ float2 transform(float2 z){
    //return vec2(2.5 * z.x, 2.5 * z.y);
    return i(S(z));
  }

  __device__ float4 colorify(float4 v){
    return rg_swizzle(v);
  }

  __device__ float2 reduce(float2 z){
    z = vec2((z.x + 1.0) / 2.0, (z.y + 1.0) / 2.0);
    return vec2((z.x - floorf(z.x)) * 2.0 - 1.0, (z.y - floorf(z.y)) * 2.0 - 1.0);
  }

  __global__ void kernel_fb(float4* out, ulong out_pitch, uchar4* pbo, int kernel_dim)
  {
    unsigned int x = blockIdx.x*blockDim.x + threadIdx.x;
    unsigned int y = blockIdx.y*blockDim.y + threadIdx.y;

    float nn = 4;
    float4 result = vec4(0.0, 0.0, 0.0, 0.0);

    float2 z = vec2(2.0 * (x + 0.5 ) / kernel_dim - 1.0, 2.0 * (y + 0.5 ) / kernel_dim - 1.0);    	

    float2 _c = vec2(0.0, 0.0);
    for(_c.x = -1.0 / kernel_dim; _c.x <= 1.0 / kernel_dim; _c.x += 2.0 / (kernel_dim * (nn - 1.0)))
      for(_c.y = -1.0 / kernel_dim; _c.y <= 1.0 / kernel_dim; _c.y += 2.0 / (kernel_dim * (nn - 1.0))){

	float2 z_c = reduce(transform(z + _c));   

	float4 frame = tex2D(input_texture, (z_c.x + 1.0) / 2.0, (z_c.y + 1.0) / 2.0);    

	float4 seed = get_seed(z_c);    

	result = result ^ (seed.w % seed) ^ ((1.0 - seed.w) % frame); 

      }
    
    result = colorify((1.0 / (nn * nn)) % result);

    //int i = 0;
    //for(i = 0; i < 500; i++)
    //    result.y += 0.00001;

    // set output variable
    out[y * out_pitch + x] = result;
    pbo[y * kernel_dim + x] = make_uchar4(255.0 * result.x, 255.0 * result.y, 255.0 * result.z, 255.0 * result.w); 
  }

}
