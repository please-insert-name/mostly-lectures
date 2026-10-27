using System;
using System.Drawing;

namespace Demo
{
    internal class Program
    {
        private static int[] _center = {0, 0};
        private static int _radius;
        private static double _aperture = 190.0 / 360.0 * 2 * Math.PI;
        
        public static void Main(string[] args)
        {
            var path = System.Reflection.Assembly.GetExecutingAssembly().Location;
            path = path.Substring(0, path.Length - 8);
            
            var bmp = new Bitmap(path + "raw.bmp");
            var processed = new Bitmap(bmp.Width, bmp.Height);

            _center[0] = bmp.Width / 4;
            _center[1] = bmp.Height / 2;
            _radius = _center[0];

            double stepx = 1.0 / bmp.Width;
            double stepy = 1.0 / bmp.Height;

            //stepy = 0.2;
            
            for (double x = 0; x < 1; x = x + stepx)
            {
                for (double y = -1; y < 1; y = y + stepy)
                {                   
                    double[] proc = ReverseCalculation(x, y);

                    if ((proc[0] * proc[0] + proc[1]*proc[1]) > 1)
                    {
                        continue;
                    }

                    // sphere 1
                    Color col = bmp.GetPixel((int) (proc[0] * _radius + _center[0]),
                        (int) (proc[1] * _radius + _center[1]));

                    var offset = -_radius;
                    if (x > 0.5)
                    {
                        offset = 3 * _radius;
                    }
                    
                    processed.SetPixel((int)(2 * (1 - x) * _radius) + offset, (int)(y * _radius + _center[1]), col);
                    //processed.SetPixel((int)(2 * (1 - x) * _radius) + offset, (int)(y * _radius + _center[1]), Color.Blue);
                    //processed.SetPixel((int) (proc[0] * _radius + _center[0]),
                    //    (int) (proc[1] * _radius + _center[1]), Color.Red);
                    
                    // sphere 2
                    col = bmp.GetPixel((int) (proc[0] * _radius + _center[0] + 2 * _radius),
                        (int) (proc[1] * _radius + _center[1]));

                    offset =  _radius;
                    
                    processed.SetPixel((int)(2 * (1 - x) * _radius) + offset, (int)(y * _radius + _center[1]), col);
                    //processed.SetPixel((int)(2 * (1 - x) * _radius) + offset, (int)(y * _radius + _center[1]), Color.Blue);
                    //processed.SetPixel((int) (proc[0] * _radius + _center[0]),
                    //    (int) (proc[1] * _radius + _center[1]), Color.Red);
                }

            }
            
            processed.Save(path + "processed.bmp");
        }

        private static double[] ReverseCalculation(double x0, double y0)
        {
            // See: http://paulbourke.net/dome/dualfish2sphere/
            
            if (Math.Abs(x0) > 1)
            {
                return null;
            }

            if (Math.Abs(y0) > 1)
            {
                return null;
            }

            // 2d equirectangular
            var longitude = x0 * Math.PI;
            var latitude = y0 * Math.PI / 2;
            
            // 3d coords on unit sphere
            var px = Math.Cos(latitude) * Math.Cos(longitude);
            var py = Math.Cos(latitude) * Math.Sin(longitude);
            var pz = Math.Sin(latitude);
            
            // 2d fisheye polar coords
            var r = 2 * Math.Atan2(Math.Sqrt(px * px + pz * pz), py) / _aperture;
            var theta = Math.Atan2(pz, px);
            
            // return 2d fisheye coords as integer
            return new[] {(r * Math.Cos(theta)), (r * Math.Sin(theta))};
        }
    }
}