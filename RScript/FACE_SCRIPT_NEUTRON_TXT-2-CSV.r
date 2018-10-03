## R Script to convert Neutron probe raw data to level 1 CSV format.
## Author: Teresa Gimeno, teresa.gimeno@bc3research.org

library(lubridate)
library(reshape)

args = commandArgs(trailingOnly=TRUE)

print(args[1])


# function to calibrate VWC vs neutron probe count data
calib_coeff <- function() {
  # Calibration coefficients according to the in-house empirical calibration. 
  # Last sample round 24-09-2013
  NP.cal <- read.csv("NP.cal2.csv")
  #calibration for clay and non-clay soils is slightly different
  up <- lm(VWC ~ NP.count, data = subset(NP.cal, Texture != "Clay"))
  clay <- lm(VWC ~ NP.count, data = subset(NP.cal, Texture == "Clay"))
  ret <- list(up,clay)
  return(ret)
}

# Read a neutron probe .txt file and convert to long-form data.frame
readfile <- function(filename, write_to_file=T) {
  print(filename)
  dat <- read.table(args[1],skip=24)
  names(dat) <- c("Probe.ID","C","missing","450", "400", "350", "300", "250", "200", "150", "125", "100", "75", "50", "25")
  datestr <- substr(filename,nchar(filename)-9,nchar(filename)-4)
  #dat$Date <- as.Date(parse_date_time(datestr,"d m y"))
  dat$Date <- as.Date(parse_date_time(datestr,"y m d"))
  dat.long <- reshape(dat, varying = c(names(dat)[4:15]),
                      idvar = c("Date", "Probe.ID"), 
                      timevar = "Depth", time=c(names(dat)[4:15]), 
                      v.names = "NP.count", direction="long") 
  dat.long <- dat.long[,-c(2,3)]                   
  ringprobe <- data.frame(Probe.ID=c(11, 12, 13, 21, 22, 31, 32, 41, 42, 43, 51, 52, 61, 62, 63), 
                          Ring=c("R1", "R1", "Outside 1", "R2", "R2", "R3", "R3", "R4", "R4", "Outside 4", "R5", "R5", "R6", "R6", "Outside 6"), Location = c("Elevated", "Elevated", "Outside", "Ambient","Ambient","Ambient","Ambient","Elevated", "Elevated", "Outside", "Elevated", "Elevated","Ambient","Ambient", "Outside"), CO2=c("Elevated", "Elevated", "Ambient", "Ambient","Ambient","Ambient","Ambient","Elevated", "Elevated", "Ambient", "Elevated", "Elevated","Ambient","Ambient", "Ambient"))
  np <- merge(ringprobe, dat.long, by = 'Probe.ID', all.y = TRUE)
  np$Depth <- as.numeric(as.character(np$Depth))
  np$NP.count[np$NP.count==0] <- NA

  # convert counts in NP txt file to VWC
  # Get calibration coefficients
  cal <- calib_coeff()
  cal.up <- cal[[1]]
  cal.clay <- cal[[2]]
  
  #Convert from NP raw count to VWC using the in-house calibration for each texture class (clay & non-clay)
  np.upper <- subset(np, Depth <= 300)
  np.upper$VWC <- coefficients(cal.up)[1] + coefficients(cal.up)[2] * np.upper$NP.count 
  np.clay <- subset(np, Depth >= 350 )
  np.clay$VWC <- coefficients(cal.clay)[1] + coefficients(cal.clay)[2] * np.clay$NP.count
  np <- rbind(np.upper, np.clay)
  
  #merge with Bulk density data - use more recent? 
  bulkDen <- read.csv('Bulk.den.csv')[, c(1, 2, 5)]
  np <- merge(np, bulkDen, by.x = c("Probe.ID", "Depth"),by.y = c("Probe.ID", "Up.depth"), 
              all.x = TRUE, all.y = FALSE)
  
  #calculate Gravimetric water content = VWC/bulkDen
  np$GWC <- np$VWC/np$Bulk.den
  
  if (write_to_file) {
    newfile <- substr(filename,1,nchar(filename)-4)
    #newfile <- paste0(newfile,"_L1.csv")
    newfile <- paste0(newfile,".csv")
    write.csv(np,file=newfile)
  }
  return(np)
  
}


readfile(args[1])
