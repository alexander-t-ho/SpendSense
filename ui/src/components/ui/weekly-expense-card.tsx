import * as React from "react";

import { motion, AnimatePresence } from "framer-motion";

import { cn } from "../../lib/utils";

import { Card, CardContent, CardHeader } from "./card";

import { Button } from "./button";



// Defines the shape of a single expense item

export interface ExpenseItem {

  category: string;

  percentage: number;

  amount: number;

  color: string; // HSL color string e.g., "221.2 83.2% 53.3%"

}



// Defines the props for the WeeklyExpenseCard component

export interface WeeklyExpenseCardProps {

  title: string;

  dateRange: string;

  data: ExpenseItem[];

  currency?: string;

  buttonText?: string;

  onButtonClick?: () => void;

  className?: string;

}



// Helper to format currency

const formatCurrency = (amount: number, currencySymbol: string) => {

  return `${currencySymbol}${amount.toFixed(2)}`;

};



/**

 * A responsive and theme-adaptive card for displaying expense summaries

 * with an animated donut chart and a clear, color-coded legend.

 * Adapted to use the current color scheme: #556B2F (green), #D4C4B0 (beige), #5D4037 (brown), #8B6F47 (tan), #F5E6D3 (light beige)

 */

export const WeeklyExpenseCard = ({

  title,

  dateRange,

  data,

  currency = "$",

  buttonText = "View Report",

  onButtonClick,

  className,

}: WeeklyExpenseCardProps) => {

  const totalAmount = React.useMemo(

    () => data.reduce((sum, item) => sum + item.amount, 0),

    [data]

  );



  // Donut chart properties

  const size = 180;

  const strokeWidth = 20;

  const radius = (size - strokeWidth) / 2;

  const circumference = 2 * Math.PI * radius;



  return (

    <Card

      className={cn(

        "w-full overflow-hidden rounded-xl p-4 font-sans shadow-xl",

        className

      )}

    >

      <CardHeader className="flex flex-row items-center justify-between p-2">

        <div className="flex flex-col">

          <h3 className="text-xl font-bold tracking-tight text-white">

            {title}

          </h3>

          <p className="text-sm text-white/90">{dateRange}</p>

        </div>

        {onButtonClick && (

          <Button 

            variant="ghost" 

            size="sm" 

            onClick={onButtonClick}

            className="text-white hover:text-white/90 hover:bg-white/10"

          >

            {buttonText}

          </Button>

        )}

      </CardHeader>



      <CardContent className="p-2">

        {/* Animated Donut Chart */}

        <div className="relative my-6 flex h-48 w-full items-center justify-center">

          <AnimatePresence>

            <motion.svg

              width={size}

              height={size}

              viewBox={`0 0 ${size} ${size}`}

              initial={{ opacity: 0 }}

              animate={{ opacity: 1, transition: { duration: 0.5 } }}

              className="-rotate-90"

            >

              {/* Background Circle */}

              <circle

                cx={size / 2}

                cy={size / 2}

                r={radius}

                fill="transparent"

                stroke="rgba(255, 255, 255, 0.2)"

                strokeWidth={strokeWidth}

              />



              {/* Data Segments - Pie Chart */}
              {data.map((item, index) => {
                // Calculate accumulated percentage up to this point (where this segment starts)
                const startPercentage = data.slice(0, index).reduce((sum, i) => sum + i.percentage, 0);
                
                // Calculate the length of this segment based on its percentage
                const segmentLength = (item.percentage / 100) * circumference;
                
                // Calculate where this segment starts on the circle (in circumference units)
                const startOffset = (startPercentage / 100) * circumference;
                
                // strokeDasharray: [visible length, gap length]
                // For a pie chart, each segment should show its length, then have a gap
                // The gap should be the rest of the circumference minus this segment
                // This ensures segments don't overlap and form a complete pie
                const dashArray = `${segmentLength} ${circumference - segmentLength}`;
                
                // strokeDashoffset: positions where the dash pattern starts
                // We rotate -90deg (via className), so we start at top
                // Offset by the start position to place each segment sequentially
                const dashOffset = circumference - startOffset;

                return (
                  <motion.circle
                    key={item.category}
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="transparent"
                    stroke={`hsl(${item.color})`}
                    strokeWidth={strokeWidth}
                    strokeDasharray={dashArray}
                    initial={{ strokeDashoffset: circumference }}
                    animate={{
                      strokeDashoffset: dashOffset,
                      transition: { duration: 0.8, ease: "easeInOut", delay: index * 0.1 },
                    }}
                    strokeLinecap="round"
                  />
                );
              })}

            </motion.svg>

          </AnimatePresence>



          {/* Central Label */}

          <div className="absolute flex flex-col items-center justify-center">

            <span className="text-xs text-white/90">Total Spent</span>

            <span className="text-2xl font-bold text-white">

              {formatCurrency(totalAmount, currency)}

            </span>

          </div>

        </div>



        {/* Legend Section */}

        <div className="mt-6 grid grid-cols-2 gap-4">

          {data.map((item) => (

            <div

              key={item.category}

              className="flex h-24 flex-col justify-end rounded-2xl bg-white/10 p-4 border border-white/20 backdrop-blur-sm"

            >

              <div className="flex items-center gap-2">

                <span

                  className="h-2.5 w-2.5 shrink-0 rounded-full"

                  style={{ backgroundColor: `hsl(${item.color})` }}

                  aria-hidden="true"

                />

                <p className="text-sm font-medium text-white/90">

                  {item.category}

                </p>

              </div>

              <p className="mt-1 text-xl font-bold text-white">

                {formatCurrency(item.amount, currency)}

              </p>

            </div>

          ))}

        </div>

      </CardContent>

    </Card>

  );

};

